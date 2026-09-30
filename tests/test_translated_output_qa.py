#!/usr/bin/env python3
"""
Integration test to verify translated chapters in the translation work directory
against Two-Pass Self-Reflection criteria and XML validity.
"""
import glob
import os
import re
import unittest
import xml.etree.ElementTree as ET

class TestTranslatedChaptersPassTwoPassQA(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.translated_dir = os.path.join(
            self.repo_root,
            "to-be-translated",
            "Quick Start Guide - John Schember_translation_work",
            "_translated",
            "text"
        )
        self.assertTrue(os.path.isdir(self.translated_dir), f"Directory {self.translated_dir} must exist")

    def test_all_chapters_are_valid_xml(self):
        """All chapters must parse as valid XML."""
        files = glob.glob(os.path.join(self.translated_dir, "*.xhtml"))
        self.assertGreater(len(files), 0, "Should have translated files")
        for f in files:
            with self.subTest(file=os.path.basename(f)):
                try:
                    tree = ET.parse(f)
                    self.assertIsNotNone(tree)
                except Exception as e:
                    self.fail(f"File {os.path.basename(f)} failed XML parse: {e}")

    def test_no_duplicate_attributes(self):
        """Check for malformed duplicate attributes like class="... class="..."."""
        files = glob.glob(os.path.join(self.translated_dir, "*.xhtml"))
        pattern = re.compile(r'class="[^"]*class="')
        for f in files:
            with self.subTest(file=os.path.basename(f)):
                with open(f, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                self.assertIsNone(pattern.search(content), f"Duplicate class attribute found in {os.path.basename(f)}")

    def test_no_demoted_headings(self):
        """Headings must not be demoted to p."""
        files = glob.glob(os.path.join(self.translated_dir, "*.xhtml"))
        demote_pattern = re.compile(r'<h([1-6])[^>]*>.*?</h\1>\s*<p class="translated">', re.DOTALL)
        for f in files:
            with self.subTest(file=os.path.basename(f)):
                with open(f, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                self.assertIsNone(demote_pattern.search(content), f"Demoted heading found in {os.path.basename(f)}")

if __name__ == '__main__':
    unittest.main()
