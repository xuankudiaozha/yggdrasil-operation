#!/usr/bin/env python3
# SENTINEL: Keep full provenance in canonical JSON and render compact search and screening summaries without per-reference detail.
"""Lightweight provenance over the existing RRA evidence inventory."""
from __future__ import annotations

import copy
from datetime import datetime
import json

from zotero_sync import deduplicate, _tokens

PROVENANCE = "rra_v6_search_provenance.md"
FACTS = ("id", "round", "source", "platform", "query", "date", "purpose", "executed", "limits",
         "hit_count", "hit_count_note", "retrieved_count", "record_ids", "raw_location")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_searches(searches, records):
    """Validate actual receipts and attach every Search ID to canonical records."""
    _require(len({s["id"] for s in searches}) == len(searches), "Search ID must be unique.")
    aliases = {}
    for record in records:
        for alias in [record["id"]] + record.get("source_record_ids", []):
            _require(alias not in aliases or aliases[alias] is record, "Source record ID belongs to multiple references.")
            aliases[alias] = record
        record["source_search_ids"] = []
        record.setdefault("screening", None)
    for search in searches:
        _require(search.get("id") and isinstance(search.get("executed"), bool), "Search ID and execution state are required.")
        if not search["executed"]:
            _require(search.get("status") == "planned" and search.get("hit_count") is None
                     and search.get("retrieved_count") is None and not search.get("record_ids"),
                     "Unexecuted searches are planned; counts must be null and records empty.")
            continue
        _require(all(search.get(k) for k in ("source", "platform", "query", "date", "purpose", "raw_location", "status")),
                 "Executed searches require source, platform, full query, time, purpose, raw location and status.")
        _require(search["status"] != "planned", "Executed searches cannot retain planned status.")
        _require("limits" in search and search["limits"] is not None, "Record actual search limits; use an empty list for none.")
        stamp = datetime.fromisoformat(search["date"].replace("Z", "+00:00"))
        _require(stamp.tzinfo is not None and stamp.utcoffset() is not None, "Search time requires an explicit timezone.")
        count = search.get("retrieved_count")
        _require(type(count) is int and count >= 0, "Retrieved count must be an actual nonnegative integer.")
        hits = search.get("hit_count")
        _require((type(hits) is int and hits >= count) or (hits is None and search.get("hit_count_note")),
                 "Unknown hits require a note; actual hits cannot be smaller than retrieved records.")
        ids = search.get("record_ids", [])
        _require(len(ids) == count and len(set(ids)) == count and set(ids) <= set(aliases),
                 "Retrieved records must match the unique raw IDs in the search receipt.")
        for record_id in ids:
            sources = aliases[record_id]["source_search_ids"]
            if search["id"] not in sources:
                sources.append(search["id"])
    _require(all(r["source_search_ids"] for r in records), "Every reference must retain an executed search source.")
    return records


def validate_screening(records, rules):
    """Reuse screening states; exclusion rules define mutually exclusive reasons."""
    _require(len({r["id"] for r in rules}) == len(rules), "Screening rule IDs must be unique.")
    generic = {"\u4e0d\u76f8\u5173", "\u8d28\u91cf\u4f4e", "irrelevant", "low quality"}
    for rule in rules:
        _require(rule.get("id") and rule.get("description") and rule["description"].strip().casefold() not in generic,
                 "Screening rules require a specific scientific description.")
    rule_ids = {r["id"] for r in rules}
    for record in records:
        status = record.get("screening")
        _require(status in (None, "include", "exclude", "uncertain"), "Unknown screening state.")
        if status in ("include", "exclude"):
            _require(record.get("screening_reason"), "Screening judgments require a reason.")
        if status == "exclude":
            _require(record.get("screening_stage") in ("title_abstract", "full_text")
                     and record.get("exclusion_rule_id") in rule_ids
                     and record["screening_reason"].strip().casefold() not in generic,
                     "Excluded references require a stage, a defined specific rule and a primary reason.")
    return records


def merge_inventory(previous, incoming):
    """Append search executions; update canonical evidence without losing origins."""
    merged = copy.deepcopy(previous or {})
    merged.update(copy.deepcopy({k: v for k, v in incoming.items() if k not in ("searches", "records")}))
    searches = merged.setdefault("searches", [])
    by_search = {s["id"]: s for s in searches}
    for search in incoming.get("searches", []):
        if search["id"] in by_search:
            old = by_search[search["id"]]
            _require(all(old.get(k) == search.get(k) for k in FACTS),
                     "Search facts are immutable; a new execution requires a new Search ID.")
            old.update(copy.deepcopy(search))
        else:
            searches.append(copy.deepcopy(search))
            by_search[search["id"]] = searches[-1]
    records = merged.setdefault("records", [])
    for fresh in incoming.get("records", []):
        old = next((r for r in records if fresh["id"] in [r["id"]] + r.get("source_record_ids", [])), None)
        if old is None:
            records.append(copy.deepcopy(fresh))
            continue
        old_tokens, fresh_tokens = _tokens(old), _tokens(fresh)
        for field in ("doi", "pmid"):
            _require(len({value for kind, value in old_tokens | fresh_tokens if kind == field}) <= 1,
                     "A canonical record update cannot replace its DOI/PMID identity.")
        if old.get("uri") and fresh.get("uri") and old["uri"] != fresh["uri"]:
            _require(any(kind in ("doi", "pmid") for kind, value in old_tokens & fresh_tokens),
                     "Changed source URI requires the same verified DOI or PMID identity.")
        identity = old["id"]
        union_fields = ("source_record_ids", "source_search_ids", "source_uris", "source_identifiers")
        retained = {key: copy.deepcopy(old.get(key, [])) for key in union_fields}
        old.update(copy.deepcopy(fresh))
        old["id"] = identity
        for key in union_fields:
            old[key] = list(retained[key])
            for value in fresh.get(key, []) + ([fresh["id"]] if key == "source_record_ids" else []):
                if value not in old[key]:
                    old[key].append(copy.deepcopy(value))
    merged["records"] = deduplicate(records)
    validate_searches(merged["searches"], merged["records"])
    validate_screening(merged["records"], merged.get("screening_rules", []))
    return merged


def summary(inv, mapping_complete=False):
    """Count one current scope, retaining unknown stages as null."""
    searches, records = copy.deepcopy(inv.get("searches", [])), copy.deepcopy(inv.get("records", []))
    problems = []
    try:
        validate_searches(searches, records)
        validate_screening(records, inv.get("screening_rules", []))
    except (ValueError, KeyError, TypeError) as error:
        problems.append(str(error))
    executed = [s for s in searches if s.get("executed")]
    valid = not problems and bool(executed)
    if not executed:
        problems.append("No executed search is available.")
    imported = sum(s["retrieved_count"] for s in executed) if valid else None
    unique = len(records) if valid else None
    if valid and imported < unique:
        problems.append("Search receipts and the unique reference inventory do not describe the same scope.")
        valid, imported, unique = False, None, None
    unknown_screening = any(r.get("screening") is None for r in records)
    if unknown_screening:
        problems.append("Screening is not complete for all acquired references.")
    if any(not s.get("executed") for s in searches):
        problems.append("Planned searches remain unexecuted.")
    included = {r["id"] for r in records if r.get("screening") == "include"}
    mapped = {e["record_id"] for p in inv.get("paragraphs", []) for e in p.get("evidence", [])}
    if mapping_complete and not mapped <= included:
        problems.append("Mapped references must belong to the current relevant inventory.")
        mapping_complete = False
    if mapping_complete and not inv.get("paragraphs"):
        mapping_complete = False
    if not mapping_complete:
        problems.append("Paragraph mapping is pending; mapped counts are unknown.")
    if any(r.get("screening") == "uncertain" for r in records):
        problems.append("Some references remain pending judgment or full-text access.")
    global_counts = {
        "imported": imported, "duplicates": imported - unique if valid else None, "unique": unique,
        "title_abstract_excluded": sum(r.get("screening") == "exclude" and r.get("screening_stage") == "title_abstract" for r in records) if valid and not unknown_screening else None,
        "full_text_excluded": sum(r.get("screening") == "exclude" and r.get("screening_stage") == "full_text" for r in records) if valid and not unknown_screening else None,
        "pending": sum(r.get("screening") in (None, "uncertain") for r in records) if valid else None,
        "relevant": len(included) if valid and not unknown_screening else None,
        "relevant_unmapped": len(included - mapped) if valid and not unknown_screening and mapping_complete else None,
        "mapped": len(mapped) if valid and mapping_complete else None,
    }
    sources = []
    for search in searches:
        rows = [r for r in records if search.get("id") in r.get("source_search_ids", [])]
        screened = not any(r.get("screening") is None for r in rows)
        ids = {r["id"] for r in rows}
        known = valid and search.get("executed")
        sources.append({"id": search.get("id"), "imported": search.get("retrieved_count") if known else None,
                        "unique": len(rows) if known else None,
                        "relevant": len(ids & included) if known and screened else None,
                        "mapped": len(ids & mapped) if known and mapping_complete else None})
    exclusions = []
    for rule in inv.get("screening_rules", []):
        for stage in ("title_abstract", "full_text"):
            ids = [r["id"] for r in records if r.get("screening") == "exclude"
                   and r.get("exclusion_rule_id") == rule["id"] and r.get("screening_stage") == stage]
            exclusions.append({"rule_id": rule["id"], "stage": stage, "count": len(ids) if valid and not unknown_screening else None,
                               "record_ids": ids})
    return {"status": "incomplete" if problems else "reconciled", "notes": problems,
            "global": global_counts, "sources": sources, "exclusions": exclusions}


def _cell(value):
    if value is None:
        return "待完成/未知"
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    return value.replace("|", "\\|").replace("\n", "<br>")


def render(inv, scope, mapping_complete=False):
    """Render a derived overview; full queries and per-reference detail stay in JSON."""
    stats = summary(inv, mapping_complete)
    lines = ["# Search Provenance & Screening Table｜检索来源与筛选表", "",
             "当前有效范围：" + (_cell(scope) if isinstance(scope, str) else "见 [当前交接](rra_v6_handoff.md) 的 research_scope。"), "",
             "规范明细：[rra_v6_evidence.json](rra_v6_evidence.json)。本文件仅为派生摘要。", "",
             "完整检索式、限制、用途及原始凭据按 Search ID 读取 searches；逐篇身份和筛选读取 records，映射读取 paragraphs。", "",
             "去重方法：规范化 DOI、PMID、精确稳定 URI 的传递匹配；保留所有 Search ID 与原始记录 ID。",
             "题名相同不自动合并；身份不确定时待核验；同一研究的不同论文报告不自动视为重复。", "",
             "来源相关数及映射数可以交叉，不能相加为全局数量。重复记录数按实际取得记录总数减去唯一文献数计算。", "",
             "| Search ID | Round | 实际时间与时区 | 数据库/来源 | 平台 | 命中数 | 实际导入数 | 相关数 | 最终映射数 | 状态 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    source_stats = {s["id"]: s for s in stats["sources"]}
    for search in inv.get("searches", []):
        counts = source_stats[search["id"]]
        values = (search["id"], search.get("round"), search.get("date"), search.get("source"), search.get("platform"),
                  search.get("hit_count"), counts["imported"], counts["relevant"], counts["mapped"], search.get("status"))
        lines.append("| " + " | ".join(_cell(v) for v in values) + " |")
    lines += ["", "## Search & Screening Summary", "", "状态：" + stats["status"], "",
              "| 统计项目 | 数量 |", "| --- | --- |"]
    labels = {"imported": "实际导入记录总数", "duplicates": "删除重复记录数", "unique": "去重后唯一文献数",
              "title_abstract_excluded": "题目/摘要筛选排除数", "full_text_excluded": "深入核验排除数", "pending": "尚未完成判断数",
              "relevant": "确认相关文献数", "relevant_unmapped": "相关但未映射数", "mapped": "最终映射参考文献数"}
    lines.extend("| " + labels[key] + " | " + _cell(value) + " |" for key, value in stats["global"].items())
    lines += ["", "相同范围的完整统计满足：导入−重复=唯一；唯一=初筛排除+深入排除+待判断+相关；相关=未映射+映射。"]
    lines.extend("- " + note for note in stats["notes"])
    lines += ["", "## 当前排除规则", "", "| 规则 | 科学边界 |", "| --- | --- |"]
    lines.extend("| " + _cell(r["id"]) + " | " + _cell(r["description"]) + " |" for r in inv.get("screening_rules", []))
    lines += ["", "## 排除数量", "", "| 规则 | 阶段 | 数量 |", "| --- | --- | --- |"]
    lines.extend("| " + " | ".join(_cell(r[k]) for k in ("rule_id", "stage", "count")) + " |" for r in stats["exclusions"])
    return "\n".join(lines) + "\n"
