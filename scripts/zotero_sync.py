#!/usr/bin/env python3
# SENTINEL: Keeps legacy evidence and Web sync contracts and probes local Zotero through a direct proxy-free connection.
"""Minimal RRA v6 Zotero Web API adapter; no academic search or manuscript writing."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class ZoteroError(RuntimeError):
    """A Zotero operation did not establish the requested library state."""


def _doi(value):
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", str(value or "").strip(), flags=re.I).lower()


def _tokens(record):
    tokens = set()
    sources = [record] + record.get("source_identifiers", [])
    for source in sources:
        if source.get("doi"):
            tokens.add(("doi", _doi(source["doi"])))
        if source.get("pmid"):
            tokens.add(("pmid", str(source["pmid"]).strip()))
        if source.get("uri"):
            tokens.add(("uri", source["uri"].strip()))
    return tokens


def _unique(values):
    result = []
    for value in values:
        if value not in result:
            result.append(copy.deepcopy(value))
    return result


def deduplicate(records):
    """Join transitive DOI/PMID/URI identities, retaining first IDs and all provenance.

    source_identifiers preserves identity bridges across repeated deduplication.
    Scientific classification remains that of the first record; source IDs and URIs
    retain the origin of merged material and extraction fields are unioned.
    """
    parent = list(range(len(records)))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    owners = {}
    for index, record in enumerate(records):
        for token in _tokens(record):
            if token in owners:
                earlier, current = root(owners[token]), root(index)
                parent[max(earlier, current)] = min(earlier, current)
            else:
                owners[token] = index
    grouped = {}
    for index, record in enumerate(records):
        grouped.setdefault(root(index), []).append(record)
    result = []
    for group in grouped.values():
        identities = set().union(*(_tokens(row) for row in group))
        conflicts = [field.upper() for field in ("doi", "pmid") if len({value for kind, value in identities if kind == field}) > 1]
        if conflicts:
            source_ids = _unique([value for row in group for value in [row["id"]] + row.get("source_record_ids", [])])
            raise ValueError("Conflicting " + "/".join(conflicts) + " identity in source records " + ", ".join(source_ids))
        merged = copy.deepcopy(group[0])
        for field in ("doi", "pmid"):
            if not merged.get(field):
                value = next((row[field] for row in group if row.get(field)), None)
                if value:
                    merged[field] = value
        if merged.get("doi"):
            merged["doi"] = _doi(merged["doi"])
        merged["source_record_ids"] = _unique([value for row in group for value in [row["id"]] + row.get("source_record_ids", [])])
        merged["source_uris"] = _unique([value for row in group for value in row.get("source_uris", []) + ([row["uri"]] if row.get("uri") else [])])
        merged["source_identifiers"] = _unique([value for row in group for value in row.get("source_identifiers", []) + [{key: row[key] for key in ("doi", "pmid", "uri") if row.get(key)}]])
        for field in ("categories", "materials", "findings", "sources", "source_search_ids"):
            if any(field in row for row in group):
                merged[field] = _unique([value for row in group for value in row.get(field, [])])
        metadata = {}
        for row in group:
            for field, value in row.get("zotero_metadata", {}).items():
                if value and not metadata.get(field):
                    metadata[field] = copy.deepcopy(value)
        if metadata:
            merged["zotero_metadata"] = metadata
        result.append(merged)
    return result


class WebZotero:
    """Authenticated personal-library Web API; injectable methods support mock tests."""

    def __init__(self):
        self.user_id = os.environ.get("ZOTERO_USER_ID", "")
        self.api_key = os.environ.get("ZOTERO_API_KEY", "")
        if not self.api_key or not self.user_id.isdigit() or int(self.user_id) == 0:
            raise ZoteroError("Set authorized ZOTERO_API_KEY and numeric ZOTERO_USER_ID; no library write attempted")

    def _request(self, method, resource, data=None, version=None):
        headers = {"Zotero-API-Key": self.api_key, "Zotero-API-Version": "3", "Accept": "application/json"}
        body = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data, ensure_ascii=False).encode("utf8")
        if version is not None:
            headers["If-Unmodified-Since-Version"] = str(version)
        elif method == "POST":
            headers["Zotero-Write-Token"] = uuid.uuid4().hex
        request = urllib.request.Request("https://api.zotero.org/users/" + self.user_id + "/" + resource, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = response.read()
                return json.loads(payload) if payload else None
        except urllib.error.HTTPError as error:
            raise ZoteroError("Zotero " + method + " failed with HTTP " + str(error.code) + "; retry only after resolving access/version/service failure") from error
        except (OSError, ValueError) as error:
            raise ZoteroError("Zotero " + method + " transport/JSON failure; verify connectivity and retry") from error

    def _list(self, resource):
        result = []
        while True:
            page = self._request("GET", resource + "?limit=100&start=" + str(len(result)))
            if not isinstance(page, list):
                raise ZoteroError("Zotero list response is not an array")
            result.extend(page)
            if len(page) < 100:
                return result

    def list_collections(self):
        return self._list("collections")

    def list_items(self):
        return self._list("items")

    def get_collection(self, key):
        return self._request("GET", "collections/" + urllib.parse.quote(key, safe=""))

    def get_item(self, key):
        return self._request("GET", "items/" + urllib.parse.quote(key, safe=""))

    def _create(self, resource, data):
        response = self._request("POST", resource, [data])
        if response.get("failed") or "0" not in response.get("successful", {}):
            raise ZoteroError("Zotero " + resource + " creation has no successful saved object")
        return response["successful"]["0"]["key"]

    def create_collection(self, name):
        return self._create("collections", {"name": name, "parentCollection": False})

    def create_item(self, record, collection_key, anchor_roles=()):
        tags = [record["source_type"]] + record.get("categories", []) + ["anchor:" + role for role in anchor_roles]
        data = {"itemType": "journalArticle", "title": record["title"], "creators": [], "url": record["uri"], "tags": [{"tag": "RRA6:" + value} for value in _unique(tags)], "collections": [collection_key], "relations": {}}
        metadata = record.get("zotero_metadata", {})
        for field in ("creators", "date", "publicationTitle", "volume", "issue", "pages", "abstractNote"):
            if field in metadata:
                data[field] = copy.deepcopy(metadata[field])
        if record.get("doi"):
            data["DOI"] = _doi(record["doi"])
        if record.get("pmid"):
            data["PMID"] = str(record["pmid"]).strip()
        return self._create("items", data)

    def add_to_collection(self, item, collection_key):
        collections = item["data"]["collections"]
        if collection_key not in collections:
            self._request("PATCH", "items/" + item["key"], {"collections": collections + [collection_key]}, version=item["version"])


def _item_identity(item):
    data = item["data"]
    return {"doi": data.get("DOI"), "pmid": data.get("PMID"), "uri": data.get("url")}


def _same_identity(record, item):
    actual = _item_identity(item)
    if not (_tokens(record) & _tokens(actual)):
        return False
    for field, normalize in (("doi", _doi), ("pmid", lambda value: str(value).strip())):
        if record.get(field) and actual.get(field) and normalize(record[field]) != normalize(actual[field]):
            return False
    return True


def _prepare(inventory, project_id):
    result = copy.deepcopy(inventory)
    if result["mode"] not in ("live", "fixture"):
        raise ValueError("Inventory mode must be live or fixture")
    result["records"] = deduplicate(result["records"])
    for record in result["records"]:
        record.pop("zotero_item_key", None)
        record.pop("fixture_item_key", None)
        record.pop("zotero_error", None)
    result["zotero_collection"] = {"status": "unavailable", "library_kind": "user", "name": "RRA6:" + project_id}
    return result


def _fixture(result):
    result["zotero_collection"]["status"] = "fixture"
    for record in result["records"]:
        if record["screening"] == "include":
            record["fixture_item_key"] = "fixture:" + record["id"]
    return result


def _verify_record(client, record, key, collection_key):
    item = client.get_item(key)
    if item["key"] != key or not _same_identity(record, item) or collection_key not in item["data"]["collections"]:
        raise ZoteroError("Readback did not confirm exact item identity and collection membership")
    record["zotero_item_key"] = item["key"]
    return item


def _unavailable(result, message):
    result["zotero_collection"]["status"] = "unavailable"
    result["zotero_collection"]["recovery"] = message
    return result


def sync_inventory(inventory, project_id, client=None):
    """Return a deep-copied inventory after narrow, retry-safe dedicated-library sync.

    Fixture mode never creates a client. Live partial failures retain successful
    keys only after readback and mark the collection status unavailable.
    """
    result = _prepare(inventory, project_id)
    if result["mode"] == "fixture":
        return _fixture(result)
    included = [row for row in result["records"] if row["screening"] == "include"]
    if not included:
        return _unavailable(result, "No included evidence records; complete screening before Zotero sync")
    try:
        client = client or WebZotero()
        result["zotero_collection"]["library_id"] = str(client.user_id)
        name = result["zotero_collection"]["name"]
        matches = [row for row in client.list_collections() if row["data"]["name"] == name]
        if len(matches) > 1:
            raise ZoteroError("Multiple project-named collections exist; identify the intended collection before retry")
        collection_key = matches[0]["key"] if matches else client.create_collection(name)
        collection = client.get_collection(collection_key)
        if collection["key"] != collection_key or collection["data"]["name"] != name:
            raise ZoteroError("Collection readback did not confirm project identity")
        result["zotero_collection"]["key"] = collection_key
        items = client.list_items()
    except (ZoteroError, KeyError, TypeError, ValueError) as error:
        return _unavailable(result, str(error))
    errors = []
    for record in included:
        try:
            if not _tokens(record):
                raise ZoteroError("No stable DOI, PMID or source URI; verify source identity before import")
            matches = [item for item in items if item["data"]["itemType"] not in ("attachment", "note") and _tokens(record) & _tokens(_item_identity(item))]
            if any(not _same_identity(record, item) for item in matches):
                raise ZoteroError("Shared source identifier conflicts with existing DOI/PMID metadata; reconcile identities before import")
            if len(matches) > 1:
                in_collection = [item for item in matches if collection_key in item["data"]["collections"]]
                if len(in_collection) != 1:
                    raise ZoteroError("Multiple matching library items; resolve the item identity without automatic merge")
                matches = in_collection
            if matches:
                key = matches[0]["key"]
                current = client.get_item(key)
                if not _same_identity(record, current):
                    raise ZoteroError("Existing item identity changed before membership update")
                client.add_to_collection(current, collection_key)
            else:
                roles = [anchor["role"] for anchor in result["anchors"] if anchor["record_id"] in record["source_record_ids"]]
                key = client.create_item(record, collection_key, roles)
            verified = _verify_record(client, record, key, collection_key)
            items = [item for item in items if item["key"] != key] + [verified]
        except (ZoteroError, KeyError, TypeError, ValueError) as error:
            record.pop("zotero_item_key", None)
            record["zotero_error"] = str(error)
            errors.append(record["id"] + ": " + str(error))
    if errors:
        return _unavailable(result, "; ".join(errors) + "; rerun sync after repair; verified earlier imports are reused")
    result["zotero_collection"]["status"] = "verified"
    return result


def verify_inventory(inventory, client=None):
    """Read-only fresh verification; never create a collection or update membership."""
    original = inventory.get("zotero_collection", {})
    name = original.get("name", "")
    project_id = name.removeprefix("RRA6:")
    result = _prepare(inventory, project_id)
    if result["mode"] == "fixture":
        return _fixture(result)
    try:
        if not original.get("key") or not name.startswith("RRA6:"):
            raise ZoteroError("No confirmed project collection key; run sync after resolving library access")
        client = client or WebZotero()
        if str(client.user_id) != str(original.get("library_id")):
            raise ZoteroError("Zotero user differs from the saved collection identity")
        result["zotero_collection"].update({"key": original["key"], "library_id": str(client.user_id)})
        collection = client.get_collection(original["key"])
        if collection["key"] != original["key"] or collection["data"]["name"] != name:
            raise ZoteroError("Project collection is missing or its identity changed")
        saved = {row["id"]: row for row in inventory["records"]}
        included = [row for row in result["records"] if row["screening"] == "include"]
        if not included:
            raise ZoteroError("No included evidence records")
        errors = []
        for record in included:
            try:
                key = saved[record["id"]].get("zotero_item_key")
                if not key:
                    raise ZoteroError("No saved verified Zotero key; run sync after repair")
                _verify_record(client, record, key, original["key"])
            except (ZoteroError, KeyError, TypeError, ValueError) as error:
                record["zotero_error"] = str(error)
                errors.append(record["id"] + ": " + str(error))
        if errors:
            return _unavailable(result, "; ".join(errors))
    except (ZoteroError, KeyError, TypeError, ValueError) as error:
        return _unavailable(result, str(error))
    result["zotero_collection"]["status"] = "verified"
    return result


def probe(collection_key=None):
    """Read-only fresh local preflight; availability does not prove write access."""
    result = {"web_credentials_present": bool(os.environ.get("ZOTERO_API_KEY") and os.environ.get("ZOTERO_USER_ID")), "plugin_status": None, "loopback": {}}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    routes = [("api", "/api/"), ("connector", "/connector/ping")]
    if collection_key:
        routes.append(("collection", "/api/users/0/collections/" + urllib.parse.quote(collection_key, safe="") + "/items?format=json&limit=100"))
    for name, route in routes:
        started = time.monotonic()
        try:
            with opener.open("http://127.0.0.1:23119" + route, timeout=5) as response:
                row = {"available": 200 <= response.status < 300, "status": response.status}
                if name == "api":
                    row["server_id_present"] = bool(response.headers.get("Zotero-Server-ID"))
                if name == "collection":
                    payload = json.loads(response.read())
                    row["page_count"] = len(payload)
                    row["total_results"] = response.headers.get("Total-Results")
                result["loopback"][name] = row
        except urllib.error.HTTPError as error:
            result["loopback"][name] = {"available": False, "status": error.code, "error": str(error)}
        except (OSError, ValueError) as error:
            result["loopback"][name] = {"available": False, "error": str(error)}
        result["loopback"][name]["seconds"] = round(time.monotonic() - started, 3)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read-only proxy-free Zotero preflight")
    parser.add_argument("--collection-key")
    args = parser.parse_args()
    print(json.dumps(probe(args.collection_key), ensure_ascii=False, indent=2))
