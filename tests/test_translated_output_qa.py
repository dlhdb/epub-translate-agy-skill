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
        # Target directories: always include committed micro-test-case fixtures,
        # plus the transient translation work directory if it exists locally.
        self.target_dirs = []
        fixture_dir = os.path.join(
            self.repo_root,
            "tests",
            "epub-translation-evaluator",
            "micro-test-case",
            "v2",
            "OEBPS"
        )
        if os.path.isdir(fixture_dir):
            self.target_dirs.append(fixture_dir)

        work_dir = os.path.join(
            self.repo_root,
            "to-be-translated",
            "Quick Start Guide - John Schember_translation_work",
            "_translated",
            "text"
        )
        if os.path.isdir(work_dir):
            self.target_dirs.append(work_dir)

        self.files = []
        for d in self.target_dirs:
            self.files.extend(glob.glob(os.path.join(d, "*.xhtml")))

        self.assertGreater(len(self.files), 0, "Should find at least one XHTML file across fixtures and work directories")

    def test_all_chapters_are_valid_xml(self):
        """All chapters must parse as valid XML."""
        for f in self.files:
            with self.subTest(file=os.path.basename(f)):
                try:
                    tree = ET.parse(f)
                    self.assertIsNotNone(tree)
                except Exception as e:
                    self.fail(f"File {os.path.basename(f)} failed XML parse: {e}")

    def test_no_duplicate_attributes(self):
        """Check for malformed duplicate attributes like class="... class="..."."""
        pattern = re.compile(r'class="[^"]*class="')
        for f in self.files:
            with self.subTest(file=os.path.basename(f)):
                with open(f, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                self.assertIsNone(pattern.search(content), f"Duplicate class attribute found in {os.path.basename(f)}")

    def test_no_demoted_headings(self):
        """Headings must not be demoted to p."""
        demote_pattern = re.compile(r'<h([1-6])[^>]*>.*?</h\1>\s*<p[^>]*class="[^"]*\btranslated\b[^"]*"', re.DOTALL)
        for f in self.files:
            with self.subTest(file=os.path.basename(f)):
                with open(f, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                self.assertIsNone(demote_pattern.search(content), f"Demoted heading found in {os.path.basename(f)}")

if __name__ == '__main__':
    unittest.main()
