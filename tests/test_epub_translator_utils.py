#!/usr/bin/env python3
"""
Unit tests for ePub Chapter Translation Utilities (epub_translator_utils.py).
Verifies:
1. extract: Correctly extracts leaf translatable blocks (ignoring parent containers with child blocks).
2. chunking: Correctly breaks down blocks into chunks by count or character threshold.
3. inject (pure mode): Correctly replaces text while preserving surrounding HTML.
4. inject (bilingual mode): Correctly inserts matching tags with class='translated',
   preserving heading levels (h1 -> h1) and stripping duplicate IDs.
5. sanitize: Escapes raw & and < while preserving valid XML entities and converting &nbsp;.
6. merge: Correctly merges chunked JSON translation files.
7. Compatibility with format_linter: Injected bilingual outputs pass all mechanical linter checks.
"""
import json
import os
import sys
import tempfile
import unittest

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scripts_dir = os.path.join(repo_root, ".agents", "skills", "awesome-epub-translator", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from epub_translator_utils import (
    extract_blocks,
    sanitize_xml,
    format_bilingual_tag,
    do_extract,
    do_inject,
    do_sanitize,
    do_merge,
)
from format_linter import lint_file


class TestEpubTranslatorUtils(unittest.TestCase):

    def setUp(self):
        self.sample_xhtml = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head><title>Sample Chapter</title></head>
<body>
  <h1 id="heading_1" class="main-title">Introduction to Strategy</h1>
  <p id="p1" class="body-text">Product management requires <span class="bold">deep thinking</span> & strategic alignment.</p>
  <ul class="points">
    <li class="item-simple">First key takeaway for teams & individuals.</li>
    <li class="item-complex"><p class="nested">Nested paragraph 1 with <a href="#ref">link</a>.</p><p class="nested">Nested paragraph 2.</p></li>
  </ul>
  <blockquote class="quote">Success is not final; failure is not fatal.</blockquote>
</body>
</html>"""

    def test_extract_leaf_blocks(self):
        blocks = extract_blocks(self.sample_xhtml)
        # Should extract h1, p1, item-simple, nested 1, nested 2, blockquote
        # Crucially, item-complex should NOT be an extracted block since it contains nested paragraphs
        tags = [b['tag'] for b in blocks.values()]
        texts = [b['text'] for b in blocks.values()]

        self.assertIn("h1", tags)
        self.assertIn("p", tags)
        self.assertIn("li", tags)
        self.assertIn("blockquote", tags)

        # Check leaf property: item-complex should not appear, its nested p's should appear
        self.assertTrue(any("Nested paragraph 1" in t for t in texts))
        self.assertTrue(any("Nested paragraph 2" in t for t in texts))
        self.assertFalse(any("Nested paragraph 1 with" in t and "Nested paragraph 2" in t for t in texts))

    def test_format_bilingual_tag(self):
        # Heading should keep heading tag, append translated class, and drop id
        tag_str = format_bilingual_tag("h1", [("id", "head1"), ("class", "main-title")], "策略導論")
        self.assertTrue(tag_str.startswith("<h1"))
        self.assertTrue(tag_str.endswith("</h1>"))
        self.assertIn('class="main-title translated"', tag_str)
        self.assertNotIn('id="head1"', tag_str)
        self.assertIn("策略導論", tag_str)

        # Paragraph without class should get class="translated"
        p_str = format_bilingual_tag("p", [], "段落譯文")
        self.assertEqual(p_str, '<p class="translated">段落譯文</p>')

    def test_sanitize_xml(self):
        raw = "AT&T and R&D with score < 10 & > 5 &nbsp; already escaped &amp; &#160;"
        sanitized = sanitize_xml(raw)

        self.assertIn("AT&amp;T", sanitized)
        self.assertIn("R&amp;D", sanitized)
        self.assertIn("&lt; 10", sanitized)
        self.assertIn("&#160;", sanitized)
        self.assertNotIn("&nbsp;", sanitized)
        # Existing escaped entities should remain unchanged
        self.assertIn("&amp;", sanitized)
        self.assertNotIn("&amp;amp;", sanitized)

    def test_inject_bilingual_and_linter_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "input.xhtml")
            json_file = os.path.join(tmpdir, "trans.json")
            out_file = os.path.join(tmpdir, "output.xhtml")

            with open(src_file, "w", encoding="utf-8") as f:
                f.write(self.sample_xhtml)

            # Extract
            blocks = extract_blocks(self.sample_xhtml)
            translations = {}
            for bid, bdata in blocks.items():
                translations[bid] = f"【譯】{bdata['text']}"

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump({"translations": translations}, f, ensure_ascii=False)

            # Inject bilingual
            class Args:
                input_html = src_file
                output_html = out_file
                translated_json = [json_file]
                mode = "bilingual"
                lang = "zh-TW"
                no_sanitize = False

            do_inject(Args())

            # Read back
            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn('xml:lang="zh-TW"', content)
            self.assertIn('lang="zh-TW"', content)
            self.assertIn('<h1 class="main-title translated">', content)
            self.assertIn('【譯】', content)
            self.assertIn("Introduction to Strategy", content)  # Original retained

            # Validate against format_linter
            linter_result = lint_file(out_file, src_file)
            self.assertEqual(linter_result["status"], "PASSED", f"Linter failed: {linter_result.get('errors')}")

    def test_inject_pure_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "input.xhtml")
            json_file = os.path.join(tmpdir, "trans.json")
            out_file = os.path.join(tmpdir, "output.xhtml")

            with open(src_file, "w", encoding="utf-8") as f:
                f.write(self.sample_xhtml)

            blocks = extract_blocks(self.sample_xhtml)
            translations = {}
            for bid in blocks.keys():
                translations[bid] = "純中文翻譯內容"

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(translations, f, ensure_ascii=False)

            class Args:
                input_html = src_file
                output_html = out_file
                translated_json = [json_file]
                mode = "pure"
                lang = "zh"
                no_sanitize = False

            do_inject(Args())

            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("純中文翻譯內容", content)
            self.assertNotIn("Introduction to Strategy", content)  # Replaced in pure mode

            linter_result = lint_file(out_file, src_file)
            self.assertEqual(linter_result["status"], "PASSED", f"Linter failed: {linter_result.get('errors')}")

    def test_chunking_and_merge(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "input.xhtml")
            manifest_file = os.path.join(tmpdir, "manifest.json")

            with open(src_file, "w", encoding="utf-8") as f:
                f.write(self.sample_xhtml)

            class ExtractArgs:
                input_html = src_file
                output_json = manifest_file
                chunk_size = 2  # 2 blocks per chunk
                max_chars = None

            do_extract(ExtractArgs())

            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            self.assertGreater(manifest["total_chunks"], 1)
            chunk_files = manifest["chunk_files"]
            self.assertEqual(len(chunk_files), manifest["total_chunks"])

            # Simulate translating chunks
            translated_chunks = []
            for idx, cfile in enumerate(chunk_files):
                with open(cfile, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                trans_map = {}
                for bid, bdata in cdata["blocks"].items():
                    trans_map[bid] = f"Trans_{bid}"
                tcfile = os.path.join(tmpdir, f"trans_chunk_{idx}.json")
                with open(tcfile, "w", encoding="utf-8") as f:
                    json.dump({"translations": trans_map}, f)
                translated_chunks.append(tcfile)

            # Test merge
            merged_json = os.path.join(tmpdir, "merged.json")
            class MergeArgs:
                output_json = merged_json
                chunk_files = translated_chunks

            do_merge(MergeArgs())

            with open(merged_json, "r", encoding="utf-8") as f:
                merged_data = json.load(f)

            self.assertEqual(len(merged_data["translations"]), manifest["total_blocks"])


if __name__ == '__main__':
    unittest.main()
