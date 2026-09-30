#!/usr/bin/env python3
"""
Tests for Two-Pass Self-Reflection Verification Rules (方案 A).
Ensures all 4 editorial QA inspection failure modes are objectively tested:
1. XML attribute syntax & duplicate attributes check.
2. Heading level preservation (preventing h1/h2 demotion to p).
3. TOC container category completeness check.
4. Pronoun and terminology consistency check.
"""
import re
import unittest
import xml.etree.ElementTree as ET

class TestTwoPassSelfReflectionRules(unittest.TestCase):

    def test_xml_attribute_cleanliness(self):
        """Pass 2 rule 1: No duplicate or malformed class attributes."""
        malformed_html = '<h2 class="center class="translated" id="task1-tr">任務 1</h2>'
        fixed_html = '<h2 class="center translated" id="task1-tr">任務 1</h2>'

        # Regex detecting duplicate class attribute pattern
        duplicate_class_pattern = re.compile(r'class="[^"]*class="')
        self.assertTrue(duplicate_class_pattern.search(malformed_html))
        self.assertFalse(duplicate_class_pattern.search(fixed_html))

        # Check valid XML parsing of the fixed version
        elem = ET.fromstring(fixed_html)
        self.assertEqual(elem.attrib.get('class'), "center translated")

    def test_heading_preservation_rule(self):
        """Pass 2 rule 2: Translated copy must preserve heading tag (h1 -> h1, not p)."""
        demoted_pair_simple = """
        <h1 class="center" id="intro">Introduction</h1>
        <p class="translated">導言</p>
        """
        demoted_pair_with_attrs = """
        <h1 class="center" id="intro">Introduction</h1>
        <p id="intro-tr" class="center translated">導言</p>
        """
        preserved_pair = """
        <h1 class="center" id="intro">Introduction</h1>
        <h1 class="center translated" id="intro-tr">導言</h1>
        """

        # Regex detects if h1-h6 is immediately followed by a <p> tag containing class="...translated..."
        demote_pattern = re.compile(r'<h([1-6])[^>]*>.*?</h\1>\s*<p[^>]*class="[^"]*\btranslated\b[^"]*"', re.DOTALL)

        self.assertTrue(bool(demote_pattern.search(demoted_pair_simple)), "Should detect simple demoted heading")
        self.assertTrue(bool(demote_pattern.search(demoted_pair_with_attrs)), "Should detect demoted heading with multiple attributes/classes")
        self.assertFalse(bool(demote_pattern.search(preserved_pair)), "Preserved pair should not be flagged as demoted")

    def test_toc_container_translation_rule(self):
        """Pass 2 rule 3: Parent category list items must also have translated counterparts."""
        missing_parent_tr = """
        <li>
          <a href="common.xhtml">Common Tasks</a>
          <ul>
            <li><a href="task1.xhtml">Task 1</a></li>
            <li class="translated"><a href="task1.xhtml">任務 1</a></li>
          </ul>
        </li>
        """
        complete_parent_tr = """
        <li>
          <a href="common.xhtml">Common Tasks</a>
          <a href="common.xhtml" class="translated">常見任務</a>
          <ul>
            <li><a href="task1.xhtml">Task 1</a></li>
            <li class="translated"><a href="task1.xhtml">任務 1</a></li>
          </ul>
        </li>
        """

        # In missing_parent_tr, the anchor is immediately followed by <ul> without a translated sibling
        has_untranslated_container = bool(re.search(r'<a href="[^"]*">([^<]+)</a>\s*<ul>', missing_parent_tr))
        complete_untranslated_container = bool(re.search(r'<a href="[^"]*">([^<]+)</a>\s*<ul>', complete_parent_tr))
        has_complete_container = bool(re.search(r'<a href="[^"]*">([^<]+)</a>\s*<a href="[^"]*" class="translated">', complete_parent_tr))

        self.assertTrue(has_untranslated_container, "Should detect untranslated parent container")
        self.assertFalse(complete_untranslated_container, "Complete container should not have untranslated anchor followed by ul")
        self.assertTrue(has_complete_container, "Should confirm presence of translated sibling anchor")

    def test_pronoun_consistency_rule(self):
        """Pass 2 rule 4: Uniform second-person address (avoid mixing '你' and '您')."""
        mixed_text = "將你的電子書傳送到電腦。如果您在歡迎精靈中設定完成..."
        unified_text = "將你的電子書傳送到電腦。如果你在歡迎精靈中設定完成..."

        def check_pronoun_mixed(text):
            has_ni = "你" in text
            has_nin = "您" in text
            return has_ni and has_nin

        self.assertTrue(check_pronoun_mixed(mixed_text), "Should detect mixed pronouns")
        self.assertFalse(check_pronoun_mixed(unified_text), "Unified text should have consistent pronoun")

if __name__ == '__main__':
    unittest.main()
