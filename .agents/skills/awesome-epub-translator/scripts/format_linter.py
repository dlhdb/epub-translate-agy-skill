#!/usr/bin/env python3
"""
Mechanical Format Linter for ePub XHTML Chapters.
Focuses strictly on deterministic structural and syntax checks:
1. XML well-formedness and closing tag validation.
2. Malformed or duplicate attributes (e.g., class="... class="...").
3. Semantic heading demotion in bilingual output (<h1> demoted to <p>).
4. HTML file truncation (missing </html>, severe content loss).

Repairs are NOT done here; precise diagnostic errors are reported so LLMs
can perform targeted, context-aware fixes.
"""

import argparse
import html.entities
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

def resolve_html_entities(text: str) -> str:
    """Pre-resolves standard HTML named entities to UTF-8 characters to prevent XML ParseError."""
    def replace_entity(match):
        ent_name = match.group(1)
        if ent_name in ("amp", "lt", "gt", "apos", "quot"):
            return match.group(0)
        char = html.entities.html5.get(ent_name + ";")
        if char:
            return char
        return match.group(0)
    return re.sub(r"&([a-zA-Z0-9]+);", replace_entity, text)

def check_xml_well_formedness(content):
    """Checks if the XHTML string is valid XML."""
    errors = []
    try:
        sanitized = resolve_html_entities(content)
        ET.fromstring(sanitized)
    except ET.ParseError as e:
        errors.append(f"XML Parse Error at line {e.position[0]}, column {e.position[1]}: {e}")
    except Exception as e:
        errors.append(f"XML Validation Error: {e}")
    return errors

def check_duplicate_attributes(content):
    """Detects duplicate or malformed attribute concatenation (e.g. class="... class="..." or class="a" class="b")."""
    errors = []
    lines = content.splitlines()
    malformed_pattern = re.compile(r'([a-zA-Z:-]+)="[^"]*\b\1="')
    tag_pattern = re.compile(r'<([a-zA-Z0-9:-]+)((?:\s+[^>]*?)?)>')

    for idx, line in enumerate(lines, start=1):
        m = malformed_pattern.search(line)
        if m:
            attr = m.group(1)
            errors.append(f"Line {idx}: Malformed/duplicate attribute '{attr}' in: {line.strip()[:100]}")
        else:
            for tag_match in tag_pattern.finditer(line):
                tag_name = tag_match.group(1)
                tag_body = tag_match.group(2)
                if not tag_body:
                    continue
                attrs = re.findall(r'\b([a-zA-Z:-]+)\s*=', tag_body)
                seen = set()
                for a in attrs:
                    if a in seen:
                        errors.append(f"Line {idx}: Duplicate attribute '{a}' in <{tag_name}> tag: {line.strip()[:100]}")
                        break
                    seen.add(a)
    return errors

def check_heading_hierarchy(content):
    """Detects bilingual heading demotions where h1-h6 is paired with p.translated instead of h1-h6."""
    errors = []
    # Pattern matches h1-h6 followed by <p class="...translated...">
    demote_pattern = re.compile(
        r'<h([1-6])[^>]*>(.*?)</h\1>(?:\s*|<!--.*?-->)*<p([^>]*class="[^"]*\btranslated\b[^"]*"[^>]*)>',
        re.DOTALL
    )
    for match in demote_pattern.finditer(content):
        tag_level = match.group(1)
        # Calculate approximate line number from match start
        line_num = content[:match.start()].count('\n') + 1
        errors.append(
            f"Line {line_num}: Semantic heading demotion: <h{tag_level}> was translated as a <p> tag instead of <h{tag_level}>"
        )
    return errors

def check_truncation(content, source_content=None):
    """Checks for truncated content or missing closing </html>."""
    errors = []
    stripped = content.strip()
    if not stripped.endswith("</html>"):
        errors.append("File Truncation: Document does not end with closing </html> tag.")

    if source_content:
        src_len = len(source_content.strip())
        tr_len = len(stripped)
        # If source is reasonably long (> 300 chars) and translation is less than 30% of source size
        if src_len > 300 and tr_len < src_len * 0.30:
            errors.append(
                f"Suspicious Truncation: Translated content length ({tr_len} chars) is under 30% of source ({src_len} chars)."
            )
    return errors

def lint_file(target_path, source_path=None):
    """Runs all mechanical format checks on a single XHTML file."""
    if not os.path.isfile(target_path):
        return {"status": "FAILED", "file": target_path, "errors": [f"File not found: {target_path}"]}

    try:
        with open(target_path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except Exception as e:
        return {"status": "FAILED", "file": target_path, "errors": [f"Failed to read file: {e}"]}

    source_content = None
    if source_path and os.path.isfile(source_path):
        try:
            with open(source_path, "r", encoding="utf-8") as fh:
                source_content = fh.read()
        except Exception:
            pass

    errors = []
    errors.extend(check_truncation(content, source_content))
    errors.extend(check_xml_well_formedness(content))
    errors.extend(check_duplicate_attributes(content))
    errors.extend(check_heading_hierarchy(content))

    return {
        "status": "PASSED" if not errors else "FAILED",
        "file": target_path,
        "errors": errors
    }

def main():
    parser = argparse.ArgumentParser(description="Mechanical Format Linter for ePub XHTML Chapters")
    parser.add_argument("target", help="Path to the translated XHTML chapter file")
    parser.add_argument("--source", default=None, help="Path to the original source XHTML file (for truncation ratio comparison)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    result = lint_file(args.target, args.source)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["status"] == "PASSED":
            print(f"[PASS] {result['file']}: No mechanical format errors detected.")
        else:
            print(f"[FAIL] {result['file']}: {len(result['errors'])} format error(s) detected:")
            for err in result["errors"]:
                print(f"  - {err}")

    sys.exit(0 if result["status"] == "PASSED" else 1)

if __name__ == "__main__":
    main()
