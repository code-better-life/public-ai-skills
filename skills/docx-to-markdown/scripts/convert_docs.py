#!/usr/bin/env python3

import os
import glob
import re
from html.parser import HTMLParser

try:
    import mammoth
except ImportError:
    print("Missing dependency: mammoth")
    print("Install it with: python3 -m pip install mammoth")
    raise SystemExit(1)

class SimpleMarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.md_output = []
        self.ignore_content = False # Flag to ignore content (e.g. inside <style>)
        
        # Text formatting state
        self.in_bold = False
        self.in_italic = False
        self.list_depth = 0
        self.in_list_item = False
        self.current_href = None
        
        # Table handling state
        self.in_table = False
        self.table_rows = []      # List of rows, where each row is a list of cell strings
        self.current_row = []     # Current row being built
        self.current_cell = []    # Current cell content (list of strings)
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        # Ignore these tags and their content
        if tag in ['style', 'head', 'script', 'title', 'meta', 'link']:
            self.ignore_content = True
            return
            
        if self.ignore_content:
            return

        # Table Start
        if tag == 'table':
            self.in_table = True
            self.table_rows = []
            return
        elif tag == 'tr':
            if self.in_table:
                self.current_row = []
            return
        elif tag == 'td' or tag == 'th':
            if self.in_table:
                self.in_cell = True
                self.current_cell = []
            return

        # Regular Markdown formatting tags
        # If we are in a table, we capture formatting chars into the cell buffer
        # If not in table, we append to md_output
        
        target_list = self.current_cell if self.in_cell else self.md_output
        
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if not self.in_table:
                target_list.append('\n\n' + '#' * int(tag[1]) + ' ')
            else:
                target_list.append('**') # Treat headers in tables as bold
        elif tag == 'p':
            if not self.in_table:
                target_list.append('\n\n')
            else:
                target_list.append(' ') # Just space in tables
        elif tag == 'br':
            if not self.in_table:
                target_list.append('  \n')
            else:
                target_list.append('<br>') # Use HTML br in tables
        elif tag == 'b' or tag == 'strong':
            target_list.append('**')
            self.in_bold = True
        elif tag == 'i' or tag == 'em':
            target_list.append('*')
            self.in_italic = True
        elif tag == 'ul' or tag == 'ol':
            if not self.in_table:
                self.list_depth += 1
        elif tag == 'li':
            if not self.in_table:
                self.in_list_item = True
                indent = '  ' * (self.list_depth - 1)
                target_list.append('\n' + indent + '- ')
            else:
                target_list.append('• ')
        elif tag == 'a':
            for k, v in attrs:
                if k == 'href':
                    self.current_href = v
                    target_list.append('[')

    def handle_endtag(self, tag):
        if tag in ['style', 'head', 'script', 'title', 'meta', 'link']:
            self.ignore_content = False
            return

        if self.ignore_content:
            return

        # Table End
        if tag == 'table':
            self.in_table = False
            self._render_table()
            return
        elif tag == 'tr':
            if self.in_table:
                self.table_rows.append(self.current_row)
            return
        elif tag == 'td' or tag == 'th':
            if self.in_table:
                self.in_cell = False
                # Join cell content and clean it
                cell_text = "".join(self.current_cell).strip()
                cell_text = re.sub(r'\s+', ' ', cell_text) # Normalize spaces
                cell_text = cell_text.replace('|', r'\|')   # Escape pipes
                self.current_row.append(cell_text)
            return

        target_list = self.current_cell if self.in_cell else self.md_output

        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if not self.in_table:
                target_list.append('\n')
            else:
                target_list.append('**')
        elif tag == 'p':
            if not self.in_table:
                target_list.append('\n')
        elif tag == 'b' or tag == 'strong':
            target_list.append('**')
            self.in_bold = False
        elif tag == 'i' or tag == 'em':
            target_list.append('*')
            self.in_italic = False
        elif tag == 'ul' or tag == 'ol':
            if not self.in_table:
                self.list_depth -= 1
        elif tag == 'li':
            if not self.in_table:
                self.in_list_item = False
        elif tag == 'a':
            if self.current_href:
                target_list.append(f']({self.current_href})')
                self.current_href = None

    def handle_data(self, data):
        if self.ignore_content:
            return
            
        text = data.replace('\n', ' ')
        if text.strip() == '' and not self.in_bold and not self.in_italic and not self.in_cell:
            return
            
        # Compress multiple spaces usually, but be careful with code? assuming docs are prose.
        text = re.sub(r'\s+', ' ', text)
        
        target_list = self.current_cell if self.in_cell else self.md_output
        target_list.append(text)

    def _render_table(self):
        if not self.table_rows:
            return
            
        # Determine number of columns
        num_cols = 0
        for row in self.table_rows:
            num_cols = max(num_cols, len(row))
            
        if num_cols == 0:
            return
            
        self.md_output.append('\n\n')
        
        # Render rows
        for i, row in enumerate(self.table_rows):
            # Pad row if needed
            while len(row) < num_cols:
                row.append("")
                
            line = "| " + " | ".join(row) + " |"
            self.md_output.append(line + '\n')
            
            # Add separator after first row (header)
            if i == 0:
                sep = "| " + " | ".join(['---'] * num_cols) + " |"
                self.md_output.append(sep + '\n')
                
        self.md_output.append('\n')

    def get_markdown(self):
        # Join and clean up multiple newlines
        content = "".join(self.md_output)
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

def convert_file(filepath):
    # Skip temporary files (starting with ~$)
    if os.path.basename(filepath).startswith("~$"):
        return

    print(f"Processing: {filepath}")
    
    try:
        # 1. Convert docx to html using mammoth
        with open(filepath, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html_content = result.value
            messages = result.messages
            
            for message in messages:
                # Log warnings but proceed
                pass

        # 2. Parse HTML to Markdown
        parser = SimpleMarkdownParser()
        parser.feed(html_content)
        md_content = parser.get_markdown()
        
        # 3. Write Markdown file
        md_filename = os.path.splitext(filepath)[0] + ".md"
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        print(f"Created: {md_filename}")
        
    except Exception as e:
        print(f"Error converting {filepath}: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert docx files to markdown.")
    parser.add_argument("files", nargs="*", help="Specific files to convert")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursively convert all docx files in current directory")
    args = parser.parse_args()

    files_to_process = []
    
    if args.files:
        # User provided specific files
        for f in args.files:
            if os.path.exists(f):
                files_to_process.append(f)
            else:
                print(f"File not found: {f}")
    else:
        # No files provided
        if args.recursive:
            print(f"Recursively scanning for .docx files in: {os.getcwd()}")
            files_to_process = glob.glob(os.path.join(os.getcwd(), "**/*.docx"), recursive=True)
        else:
            print(f"Scanning for .docx files in current directory: {os.getcwd()}")
            # Default to current directory only (non-recursive)
            files_to_process = glob.glob(os.path.join(os.getcwd(), "*.docx"))

    if not files_to_process:
        print("No .docx files found to convert.")
        return

    print(f"Found {len(files_to_process)} files to process.")
    
    for f in files_to_process:
        convert_file(f)

if __name__ == "__main__":
    main()
