#!/usr/bin/env python3
# SENTINEL: Report saved DOCX Zotero field instructions without certifying visible results, library resolution or scientific support.
"""Read-only smoke test for editable Zotero fields in DOCX XML.

Usage: python docx_zotero_probe.py manuscript.docx

Reports the count of Zotero citation/bibliography field instructions. Not a
replacement for validating live Word+Zotero behavior or source correctness.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
WORD_PART = re.compile(r"^word/(?:document|footnotes|endnotes|header\d+|footer\d+)\.xml$")
CITATION = re.compile(r"\bADDIN\s+ZOTERO_ITEM\b", re.I)
BIBLIO = re.compile(r"\bADDIN\s+ZOTERO_BIBL\b", re.I)


def get_instruction_strings(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    instructions = []
    for para in root.iter(W + "p"):
        split_field_parts = []
        for node in para.iter():
            if node.tag == W + "instrText" and node.text:
                split_field_parts.append(node.text)
            elif node.tag == W + "fldSimple":
                instruction = node.get(W + "instr", "")
                if instruction:
                    instructions.append(instruction)
        if split_field_parts:
            instructions.append("".join(split_field_parts))
    return instructions


def inspect(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Not found: {path}")
    citation_count = bibliography_count = parts = 0
    with ZipFile(path, "r") as archive:
        for name in archive.namelist():
            if not WORD_PART.fullmatch(name):
                continue
            parts += 1
            for instruction in get_instruction_strings(archive.read(name)):
                citation_count += len(CITATION.findall(instruction))
                bibliography_count += len(BIBLIO.findall(instruction))
    return {
        "file": str(path),
        "word_parts_scanned": parts,
        "zotero_citation_field_instructions": citation_count,
        "zotero_bibliography_field_instructions": bibliography_count,
        "caveat": "Structural field-presence smoke test only; not verification of Zotero connectivity, citation validity, or expected field count.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.docx), ensure_ascii=False, indent=2))
        return 0
    except (OSError, BadZipFile, ET.ParseError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
