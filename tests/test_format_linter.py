#!/usr/bin/env python3
"""
Unit tests for Mechanical Format Linter (format_linter.py).
Verifies:
1. Valid XHTML passes without errors.
2. Malformed XML fails with XML Parse Error.
3. Duplicate attributes (e.g. class="... class="...") trigger errors.
4. Semantic heading demotions (h1 -> p) trigger errors.
5. Truncation and missing </html> trigger errors.
"""
import os
import sys
import tempfile
import unittest

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scripts_dir = os.path.join(repo_root, ".agents", "skills", "awesome-epub-translator", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from format_linter import (
    lint_file,
    check_xml_well_formedness,
    check_duplicate_attributes,
    check_heading_hierarchy,
    check_truncation,
)


class TestFormatLinter(unittest.TestCase):

    def test_valid_xhtml_passes(self):
        content = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh">
<head><title>Test</title></head>
<body>
  <h1 class="center" id="intro">Introduction</h1>
  <h1 class="center translated" id="intro-tr">導言</h1>
  <p>Some text.</p>
  <p class="translated">一些文字。</p>
</body>
</html>"""
        self.assertEqual(len(check_xml_well_formedness(content)), 0)
        self.assertEqual(len(check_duplicate_attributes(content)), 0)
        self.assertEqual(len(check_heading_hierarchy(content)), 0)
        self.assertEqual(len(check_truncation(content)), 0)

    def test_broken_xml_detected(self):
        content = "<div><p>Unclosed paragraph</div>"
        errors = check_xml_well_formedness(content)
        self.assertGreater(len(errors), 0)
        self.assertIn("XML Parse Error", errors[0])

    def test_duplicate_attribute_detected(self):
        content = '<p class="content class="translated">Text</p>'
        errors = check_duplicate_attributes(content)
        self.assertGreater(len(errors), 0)
        self.assertIn("Malformed/duplicate attribute 'class'", errors[0])

    def test_duplicate_distinct_attribute_detected(self):
        content = '<p class="foo" class="bar">Text</p>'
        errors = check_duplicate_attributes(content)
        self.assertGreater(len(errors), 0)
        self.assertIn("Duplicate attribute 'class' in <p> tag", errors[0])

    def test_html_entities_pass_without_error(self):
        content = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh">
<body>
  <p>&copy; 2026 Test &mdash; All rights reserved.&nbsp;&hellip;</p>
  <p>Standard XML: &amp; &lt; &gt; &apos; &quot;</p>
</body>
</html>"""
        errors = check_xml_well_formedness(content)
        self.assertEqual(len(errors), 0)

    def test_heading_demotion_detected(self):
        content = """
        <h2 class="title">Chapter 1</h2>
        <!-- divider -->
        <p class="title translated">第一章</p>
        """
        errors = check_heading_hierarchy(content)
        self.assertGreater(len(errors), 0)
        self.assertIn("Semantic heading demotion: <h2> was translated as a <p>", errors[0])

    def test_truncation_missing_html_tag(self):
        content = "<html><body><p>Unfinished"
        errors = check_truncation(content)
        self.assertGreater(len(errors), 0)
        self.assertIn("does not end with closing </html>", errors[0])

    def test_suspicious_length_truncation(self):
        source = "<p>" + ("long original content sentence. " * 30) + "</p></html>"
        truncated = "<p>短</p></html>"
        errors = check_truncation(truncated, source_content=source)
        self.assertGreater(len(errors), 0)
        self.assertIn("Suspicious Truncation", errors[0])

    def test_lint_file_end_to_end(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".xhtml", delete=False) as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<body>
  <h1>Title</h1>
  <p class="translated">標題</p>
</body>
</html>""")
            f_path = f.name

        try:
            result = lint_file(f_path)
            self.assertEqual(result["status"], "FAILED")
            self.assertIn("Semantic heading demotion", result["errors"][0])
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)


if __name__ == "__main__":
    unittest.main()
