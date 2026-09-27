import html.parser
import sys
import json
import os

class HTMLValidator(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.void_elements:
            return
        if not self.stack:
            self.errors.append(f"Unexpected closing tag: </{tag}>")
            return
        expected = self.stack.pop()
        if tag != expected:
            self.errors.append(f"Mismatched tag: expected </{expected}>, got </{tag}>")

    def handle_startendtag(self, tag, attrs):
        pass

def check_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    validator = HTMLValidator()
    try:
        validator.feed(content)
        if validator.stack:
            validator.errors.append(f"Unclosed tags remaining: {', '.join(validator.stack)}")
    except Exception as e:
        validator.errors.append(f"Parse error: {e}")
        
    is_valid = len(validator.errors) == 0
    return is_valid, validator.errors

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No directory provided"}))
        sys.exit(1)
        
    target_dir = sys.argv[1]
    if not os.path.isdir(target_dir):
        print(json.dumps({"error": f"Directory not found: {target_dir}"}))
        sys.exit(1)

    results = {}
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(('.html', '.xhtml')):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, target_dir)
                is_valid, errors = check_file(filepath)
                results[rel_path] = {
                    "valid": is_valid,
                    "errors": errors
                }
                
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
