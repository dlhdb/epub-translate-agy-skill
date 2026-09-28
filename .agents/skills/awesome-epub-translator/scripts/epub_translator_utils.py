#!/usr/bin/env python3
import sys
import json
import os
from html.parser import HTMLParser

class OffsetParser(HTMLParser):
    def __init__(self, html_content):
        super().__init__()
        self.html = html_content
        self.lines = html_content.splitlines(keepends=True)
        # Block level tags that usually contain translatable text
        self.block_tags = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'figcaption', 'dt', 'dd', 'title'}
        
        self.blocks = {}
        self.active_tag = None
        self.active_start_pos = -1
        self.counter = 1

    def get_absolute_pos(self, line, offset):
        # line is 1-indexed
        return sum(len(l) for l in self.lines[:line-1]) + offset

    def handle_starttag(self, tag, attrs):
        if tag in self.block_tags and self.active_tag is None:
            self.active_tag = tag
            line, col = self.getpos()
            abs_pos = self.get_absolute_pos(line, col)
            
            # Find the end of this start tag
            end_of_start_tag = self.html.find('>', abs_pos) + 1
            self.active_start_pos = end_of_start_tag

    def handle_endtag(self, tag):
        if tag == self.active_tag:
            line, col = self.getpos()
            abs_pos = self.get_absolute_pos(line, col)
            
            inner_html = self.html[self.active_start_pos:abs_pos]
            
            if inner_html.strip():
                block_id = f"agy_block_{self.counter}"
                self.blocks[block_id] = {
                    "start": self.active_start_pos,
                    "end": abs_pos,
                    "text": inner_html
                }
                self.counter += 1
                
            self.active_tag = None


def extract(html_path, json_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    parser = OffsetParser(content)
    parser.feed(content)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(parser.blocks, f, ensure_ascii=False, indent=2)
    
    print(f"Extracted {len(parser.blocks)} translatable blocks to {json_path}")


def inject(original_html_path, translated_json_path, out_html_path):
    with open(original_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    with open(translated_json_path, 'r', encoding='utf-8') as f:
        blocks = json.load(f)
        
    # Sort blocks by start offset in DESCENDING order
    # This is crucial so that string replacements don't shift the offsets of earlier blocks
    sorted_blocks = sorted(blocks.values(), key=lambda b: b['start'], reverse=True)
    
    for block in sorted_blocks:
        start = block['start']
        end = block['end']
        translated_text = block['text']
        
        # Replace the substring
        content = content[:start] + translated_text + content[end:]
        
    # Update lang attributes for good measure
    content = content.replace('<html xmlns="http://www.w3.org/1999/xhtml"', '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh" lang="zh"')
        
    with open(out_html_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully injected translations and wrote to {out_html_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 epub_translator_utils.py [extract|inject] ...")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == 'extract':
        if len(sys.argv) != 4:
            print("Usage: python3 epub_translator_utils.py extract <input_html> <output_json>")
            sys.exit(1)
        extract(sys.argv[2], sys.argv[3])
    elif mode == 'inject':
        if len(sys.argv) != 5:
            print("Usage: python3 epub_translator_utils.py inject <original_html> <translated_json> <output_html>")
            sys.exit(1)
        inject(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Unknown mode")
