#!/usr/bin/env python3
"""
ePub Chapter Translation Utilities.

Provides deterministic, zero-external-dependency operations for ePub XHTML translation:
1. extract: Parses XHTML to extract translatable text blocks and structural metadata into JSON.
   Supports automatic chunking for very large chapters.
2. inject: Reassembles translated text back into XHTML with 100% structural fidelity.
   Supports both 'pure' (replace original) and 'bilingual' (interleave original + translated) modes.
3. sanitize: Deterministic XML/XHTML character entity escaping (&, <, >, &nbsp;) ensuring well-formedness.
4. merge: Merges multiple translated chunk JSON files into a single unified JSON file.
"""

import argparse
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

BLOCK_TAGS = {
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'li', 'td', 'th', 'blockquote', 'figcaption',
    'dt', 'dd', 'title'
}

VOID_TAGS = {
    'area', 'base', 'br', 'col', 'embed', 'hr',
    'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'
}


class RobustBlockParser(HTMLParser):
    """
    Parser that records block-level element boundaries and attributes.
    Accurately identifies leaf translatable blocks, skipping parent containers
    when children blocks exist to prevent duplicate translations.
    """

    def __init__(self, html_content):
        super().__init__()
        self.html = html_content
        self.lines = html_content.splitlines(keepends=True)
        self.tag_stack = []
        self.raw_blocks = []

    def get_abs_pos(self, line, col):
        return sum(len(l) for l in self.lines[:line - 1]) + col

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in VOID_TAGS:
            return
        line, col = self.getpos()
        pos = self.get_abs_pos(line, col)
        tag_end = self.html.find('>', pos) + 1
        self.tag_stack.append({
            'tag': tag_lower,
            'attrs': attrs,
            'outer_start': pos,
            'inner_start': tag_end
        })

    def handle_startendtag(self, tag, attrs):
        # Void / self-closing tags (<br/>, <img/>, etc.) have no inner content to translate
        pass

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in VOID_TAGS:
            return
        line, col = self.getpos()
        pos = self.get_abs_pos(line, col)
        tag_end = self.html.find('>', pos) + 1

        for i in range(len(self.tag_stack) - 1, -1, -1):
            if self.tag_stack[i]['tag'] == tag_lower:
                elem = self.tag_stack.pop(i)
                elem['inner_end'] = pos
                elem['outer_end'] = tag_end

                if tag_lower in BLOCK_TAGS:
                    inner = self.html[elem['inner_start']:elem['inner_end']]
                    if inner.strip():
                        elem['text'] = inner
                        self.raw_blocks.append(elem)
                break

    def get_leaf_blocks(self):
        """
        Filters raw blocks so that parent containers (e.g. <ul> or <li> containing <p>)
        are not extracted if their children are already translatable blocks.
        """
        leaf_blocks = []
        for b in self.raw_blocks:
            is_parent = False
            for other in self.raw_blocks:
                if other is not b and b['outer_start'] <= other['outer_start'] and other['outer_end'] <= b['outer_end']:
                    is_parent = True
                    break
            if not is_parent:
                leaf_blocks.append(b)

        leaf_blocks.sort(key=lambda x: x['outer_start'])
        return leaf_blocks


def sanitize_xml(content):
    """
    Sanitizes XML content by escaping raw & and < characters that would break XML parsers.
    Also normalizes &nbsp; to &#160;.
    """
    # 1. Normalize non-standard entity &nbsp; to numeric entity &#160;
    content = content.replace('&nbsp;', '&#160;')

    # 2. Escape unescaped ampersands: & not followed by a valid XML entity name or character ref
    content = re.sub(r'&(?!(?:[a-zA-Z]+|#[0-9]+|#x[0-9a-fA-F]+);)', '&amp;', content)

    # 3. Escape stray less-than signs: < not followed by a tag name character, /, !, or ?
    content = re.sub(r'<(?!(?:/?[a-zA-Z]|!|\?))', '&lt;', content)

    return content


def format_bilingual_tag(tag, attrs, translated_text):
    """
    Constructs a matching translated tag for bilingual mode.
    - Matches the original element tag type (e.g., <h1...> -> <h1...>, <p...> -> <p...>)
    - Omits id attribute to avoid HTML duplicate ID errors
    - Appends 'translated' to class attribute
    """
    attr_parts = []
    has_class = False

    for k, v in attrs:
        k_lower = k.lower()
        if k_lower == 'id':
            continue  # do not duplicate element IDs
        elif k_lower == 'class':
            has_class = True
            classes = v.split()
            if 'translated' not in classes:
                classes.append('translated')
            attr_parts.append(f'class="{" ".join(classes)}"')
        else:
            attr_parts.append(f'{k}="{v}"')

    if not has_class:
        attr_parts.append('class="translated"')

    attr_str = (' ' + ' '.join(attr_parts)) if attr_parts else ''
    return f'<{tag}{attr_str}>{translated_text}</{tag}>'


def extract_blocks(html_content):
    """Parses HTML content and returns an indexed dictionary of translatable blocks."""
    parser = RobustBlockParser(html_content)
    parser.feed(html_content)
    leaf_blocks = parser.get_leaf_blocks()

    blocks = {}
    for idx, b in enumerate(leaf_blocks, start=1):
        block_id = f"agy_block_{idx}"
        blocks[block_id] = {
            "id": block_id,
            "tag": b['tag'],
            "attrs": b['attrs'],
            "outer_start": b['outer_start'],
            "outer_end": b['outer_end'],
            "inner_start": b['inner_start'],
            "inner_end": b['inner_end'],
            "text": b['text']
        }
    return blocks


def do_extract(args):
    with open(args.input_html, 'r', encoding='utf-8') as f:
        html_content = f.read()

    blocks = extract_blocks(html_content)

    # Check if chunking is requested
    chunk_size = args.chunk_size
    max_chars = args.max_chars

    if chunk_size or max_chars:
        chunks = []
        current_chunk = {}
        current_chars = 0
        current_count = 0

        for block_id, bdata in blocks.items():
            text_len = len(bdata['text'])
            split_needed = False

            if chunk_size and current_count >= chunk_size:
                split_needed = True
            if max_chars and current_chars + text_len > max_chars and current_count > 0:
                split_needed = True

            if split_needed:
                chunks.append(current_chunk)
                current_chunk = {}
                current_chars = 0
                current_count = 0

            current_chunk[block_id] = bdata
            current_chars += text_len
            current_count += 1

        if current_chunk:
            chunks.append(current_chunk)

        base_out, ext = os.path.splitext(args.output_json)
        created_files = []
        for idx, chunk in enumerate(chunks, start=1):
            chunk_file = f"{base_out}_chunk_{idx:02d}{ext}"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                json.dump({"blocks": chunk, "chunk_index": idx, "total_chunks": len(chunks)}, f, ensure_ascii=False, indent=2)
            created_files.append(chunk_file)

        manifest_file = args.output_json
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump({
                "source_file": args.input_html,
                "total_blocks": len(blocks),
                "total_chunks": len(chunks),
                "chunk_files": created_files,
                "blocks": blocks
            }, f, ensure_ascii=False, indent=2)

        print(f"Extracted {len(blocks)} blocks into {len(chunks)} chunks.")
        print(f"Manifest: {manifest_file}")
    else:
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump({"blocks": blocks, "total_blocks": len(blocks)}, f, ensure_ascii=False, indent=2)
        print(f"Extracted {len(blocks)} translatable blocks to {args.output_json}")


def do_inject(args):
    with open(args.input_html, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Re-extract blocks from input HTML to get exact offsets
    blocks = extract_blocks(html_content)

    # Load translated texts from one or more JSON files
    translations = {}
    for json_path in args.translated_json:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Support various JSON payload formats
        if isinstance(data, dict):
            if "translations" in data and isinstance(data["translations"], dict):
                translations.update(data["translations"])
            elif "blocks" in data and isinstance(data["blocks"], dict):
                for k, v in data["blocks"].items():
                    if isinstance(v, dict) and "translated" in v:
                        translations[k] = v["translated"]
                    elif isinstance(v, dict) and "text" in v:
                        translations[k] = v["text"]
                    elif isinstance(v, str):
                        translations[k] = v
            else:
                for k, v in data.items():
                    if isinstance(v, str):
                        translations[k] = v
                    elif isinstance(v, dict) and "translated" in v:
                        translations[k] = v["translated"]

    mode = args.mode  # 'pure' or 'bilingual'
    target_lang = args.lang

    # Process blocks in reverse order of outer_end / inner_start so offsets remain stable
    sorted_blocks = sorted(blocks.values(), key=lambda b: b['outer_start'], reverse=True)

    result_content = html_content
    injected_count = 0

    for b in sorted_blocks:
        b_id = b['id']
        translated_text = translations.get(b_id)
        if not translated_text:
            # If not translated, skip
            continue

        injected_count += 1
        if mode == 'bilingual':
            translated_tag_str = format_bilingual_tag(b['tag'], b['attrs'], translated_text)
            # Insert immediately after the original tag's outer_end
            pos = b['outer_end']
            result_content = result_content[:pos] + "\n" + translated_tag_str + result_content[pos:]
        else:
            # 'pure' mode: replace inner content
            result_content = result_content[:b['inner_start']] + translated_text + result_content[b['inner_end']:]

    # Update lang attributes in <html>
    if target_lang:
        # Update existing lang and xml:lang attributes or insert them
        html_tag_match = re.search(r'<html\b([^>]*)>', result_content, re.IGNORECASE)
        if html_tag_match:
            original_attrs = html_tag_match.group(1)
            new_attrs = original_attrs
            if 'xml:lang=' in new_attrs:
                new_attrs = re.sub(r'xml:lang="[^"]*"', f'xml:lang="{target_lang}"', new_attrs)
            else:
                new_attrs += f' xml:lang="{target_lang}"'

            if re.search(r'\blang="[^"]*"', new_attrs):
                new_attrs = re.sub(r'\blang="[^"]*"', f'lang="{target_lang}"', new_attrs)
            else:
                new_attrs += f' lang="{target_lang}"'

            result_content = result_content[:html_tag_match.start()] + f'<html{new_attrs}>' + result_content[html_tag_match.end():]

    # Auto-sanitize XML unless disabled
    if not args.no_sanitize:
        result_content = sanitize_xml(result_content)

    os.makedirs(os.path.dirname(os.path.abspath(args.output_html)), exist_ok=True)
    with open(args.output_html, 'w', encoding='utf-8') as f:
        f.write(result_content)

    print(f"Successfully injected {injected_count}/{len(blocks)} blocks ({mode} mode) into {args.output_html}")


def do_sanitize(args):
    with open(args.input_html, 'r', encoding='utf-8') as f:
        content = f.read()

    sanitized = sanitize_xml(content)
    out_path = args.output_html if args.output_html else args.input_html

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(sanitized)

    print(f"Sanitized XML written to {out_path}")


def do_merge(args):
    merged_translations = {}
    for fpath in args.chunk_files:
        with open(fpath, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        if "translations" in data and isinstance(data["translations"], dict):
            merged_translations.update(data["translations"])
        elif "blocks" in data and isinstance(data["blocks"], dict):
            for k, v in data["blocks"].items():
                if isinstance(v, dict) and "translated" in v:
                    merged_translations[k] = v["translated"]
                elif isinstance(v, dict) and "text" in v:
                    merged_translations[k] = v["text"]
                elif isinstance(v, str):
                    merged_translations[k] = v
        elif isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    merged_translations[k] = v
                elif isinstance(v, dict) and "translated" in v:
                    merged_translations[k] = v["translated"]

    with open(args.output_json, 'w', encoding='utf-8') as fh:
        json.dump({"translations": merged_translations}, fh, ensure_ascii=False, indent=2)

    print(f"Merged {len(merged_translations)} translated blocks from {len(args.chunk_files)} chunks into {args.output_json}")


def main():
    parser = argparse.ArgumentParser(description="ePub Translation Utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # extract
    p_extract = subparsers.add_parser("extract", help="Extract translatable blocks to JSON")
    p_extract.add_argument("input_html", help="Path to input XHTML file")
    p_extract.add_argument("output_json", help="Path to output JSON file")
    p_extract.add_argument("--chunk-size", type=int, default=None, help="Number of blocks per chunk")
    p_extract.add_argument("--max-chars", type=int, default=None, help="Max character count per chunk")
    p_extract.set_defaults(func=do_extract)

    # inject
    p_inject = subparsers.add_parser("inject", help="Inject translated blocks into XHTML")
    p_inject.add_argument("input_html", help="Path to original XHTML file")
    p_inject.add_argument("output_html", help="Path to output XHTML file")
    p_inject.add_argument("translated_json", nargs="+", help="One or more translated JSON files")
    p_inject.add_argument("--mode", choices=["pure", "bilingual"], default="pure", help="Translation mode (default: pure)")
    p_inject.add_argument("--lang", default="zh", help="Target language code for <html> tag (default: zh)")
    p_inject.add_argument("--no-sanitize", action="store_true", help="Disable automatic XML sanitization")
    p_inject.set_defaults(func=do_inject)

    # sanitize
    p_sanitize = subparsers.add_parser("sanitize", help="Sanitize XML special characters (&, <, >)")
    p_sanitize.add_argument("input_html", help="Path to XHTML file to sanitize")
    p_sanitize.add_argument("output_html", nargs="?", default=None, help="Output path (defaults to overwrite input)")
    p_sanitize.set_defaults(func=do_sanitize)

    # merge
    p_merge = subparsers.add_parser("merge", help="Merge multiple chunk JSONs into a single JSON")
    p_merge.add_argument("output_json", help="Path to merged output JSON")
    p_merge.add_argument("chunk_files", nargs="+", help="Chunk JSON files to merge")
    p_merge.set_defaults(func=do_merge)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
