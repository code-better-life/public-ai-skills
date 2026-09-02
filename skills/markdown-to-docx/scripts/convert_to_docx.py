#!/usr/bin/env python3
"""
Markdown to Word (公文格式) Converter
Converts Markdown files to Word documents with Chinese official document formatting.
Also supports formatting existing .docx files.
"""

import os
import re
import argparse

try:
    from docx import Document
    from docx.shared import Pt, Cm, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.section import WD_ORIENT
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("Missing dependency: python-docx")
    print("Install it with: python3 -m pip install python-docx")
    raise SystemExit(1)

# ============================================================================
# Configuration: Official Document Formatting Standards (公文排版格式规范)
# ============================================================================

# Page margins (cm)
MARGIN_TOP = 3.7
MARGIN_BOTTOM = 3.5
MARGIN_LEFT = 2.8
MARGIN_RIGHT = 2.6

# Header/Footer distance (cm)
HEADER_DISTANCE = 1.5
FOOTER_DISTANCE = 2.5

# Font sizes (Chinese convention: 二号=22pt, 三号=16pt, 四号=14pt)
SIZE_TITLE = 22  # 二号
SIZE_BODY = 16   # 三号
SIZE_PAGE_NUM = 14  # 四号

# Line spacing (pt)
LINE_SPACING_TITLE = 35
LINE_SPACING_BODY = 30

# Font names with fallbacks
FONTS = {
    'title': ['方正小标宋简体', 'SimSun', '宋体'],  # Document title
    'h1': ['SimHei', '黑体'],                       # 一级标题
    'h2': ['楷体_GB2312', 'KaiTi', '楷体'],         # 二级标题
    'h3': ['仿宋_GB2312', 'FangSong', '仿宋'],      # 三级标题
    'body': ['仿宋_GB2312', 'FangSong', '仿宋'],    # 正文
    'page_num': ['宋体', 'SimSun'],                 # 页码
}


# Chinese quotation marks using Unicode escape sequences
CHINESE_LEFT_DOUBLE_QUOTE = '\u201c'   # "
CHINESE_RIGHT_DOUBLE_QUOTE = '\u201d'  # "
CHINESE_LEFT_SINGLE_QUOTE = '\u2018'   # '
CHINESE_RIGHT_SINGLE_QUOTE = '\u2019'  # '


def convert_quotes_to_chinese(text):
    """Convert English quotes to Chinese quotes (成对的上下引号)."""
    # Track quote state for proper pairing
    result = []
    in_double_quote = False
    in_single_quote = False
    
    i = 0
    while i < len(text):
        char = text[i]
        
        if char == '"':
            if in_double_quote:
                result.append(CHINESE_RIGHT_DOUBLE_QUOTE)  # Closing quote
                in_double_quote = False
            else:
                result.append(CHINESE_LEFT_DOUBLE_QUOTE)  # Opening quote
                in_double_quote = True
        elif char == "'":
            if in_single_quote:
                result.append(CHINESE_RIGHT_SINGLE_QUOTE)  # Closing single quote
                in_single_quote = False
            else:
                result.append(CHINESE_LEFT_SINGLE_QUOTE)  # Opening single quote
                in_single_quote = True
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)


def strip_markdown_formatting(text):
    """Remove all markdown formatting markers (**bold**, *italic*) from text.
    
    Used for headings which should not have any bold/italic formatting.
    """
    # Remove bold markers (**text** -> text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove italic markers (*text* -> text)
    text = re.sub(r'\*([^*]+?)\*', r'\1', text)
    return text


def normalize_heading_text(text, should_have_period):
    """Normalize heading text: strip markdown formatting and handle punctuation.
    
    Args:
        text: The heading text, may contain **bold** or *italic* markers
        should_have_period: True if heading should end with exactly one period (H2/H3),
                           False if heading should NOT have period (H1/Title)
    
    Returns:
        Plain text with correct punctuation, no markdown formatting
    """
    # First, strip all markdown formatting
    text = strip_markdown_formatting(text)
    text = text.rstrip()
    
    if not text:
        return text
    
    # Normalize numbering spaces: "1. text" -> "1.text", "(1) text" -> "(1)text"
    # Match patterns like: 1. 2. (1) (2) （一） 一、 etc. followed by extra space
    text = re.sub(r'^(\d+\.)\s+', r'\1', text)  # "1. " -> "1."
    text = re.sub(r'^(\(\d+\))\s+', r'\1', text)  # "(1) " -> "(1)"
    text = re.sub(r'^(（[一二三四五六七八九十]+）)\s+', r'\1', text)  # "（一） " -> "（一）"
    text = re.sub(r'^([一二三四五六七八九十]+、)\s+', r'\1', text)  # "一、 " -> "一、"
    
    # Remove all trailing periods (Chinese and English)
    while text and text[-1] in '。.':
        text = text[:-1]
    
    # Add period if required
    if should_have_period and text:
        text += '。'
    
    return text


def ensure_period_ending(text):
    """Ensure heading text ends with exactly one Chinese period (句号).
    
    Strips markdown formatting and ensures exactly one period at end.
    Used for H2 and H3 headings.
    """
    return normalize_heading_text(text, should_have_period=True)


def remove_trailing_period(text):
    """Remove all trailing periods from heading text.
    
    Strips markdown formatting and removes all trailing periods.
    Used for Title and H1 headings.
    """
    return normalize_heading_text(text, should_have_period=False)


# Common color name to RGB mapping
COLOR_MAP = {
    'red': RGBColor(255, 0, 0),
    'green': RGBColor(0, 128, 0),
    'blue': RGBColor(0, 0, 255),
    'yellow': RGBColor(255, 255, 0),
    'orange': RGBColor(255, 165, 0),
    'purple': RGBColor(128, 0, 128),
    'pink': RGBColor(255, 192, 203),
    'brown': RGBColor(165, 42, 42),
    'gray': RGBColor(128, 128, 128),
    'grey': RGBColor(128, 128, 128),
    'black': RGBColor(0, 0, 0),
    'white': RGBColor(255, 255, 255),
    'cyan': RGBColor(0, 255, 255),
    'magenta': RGBColor(255, 0, 255),
    'lime': RGBColor(0, 255, 0),
    'navy': RGBColor(0, 0, 128),
    'teal': RGBColor(0, 128, 128),
    'maroon': RGBColor(128, 0, 0),
    'olive': RGBColor(128, 128, 0),
    'silver': RGBColor(192, 192, 192),
    'aqua': RGBColor(0, 255, 255),
    'fuchsia': RGBColor(255, 0, 255),
}


def parse_color_value(color_str):
    """Parse a color string and return RGBColor.
    
    Supports:
    - Named colors: red, blue, green, etc.
    - Hex colors: #FF0000, #f00
    - RGB: rgb(255, 0, 0)
    
    Returns None if color cannot be parsed (will use default black).
    """
    if not color_str:
        return None
    
    color_str = color_str.strip().lower()
    
    # Named color
    if color_str in COLOR_MAP:
        return COLOR_MAP[color_str]
    
    # Hex color
    if color_str.startswith('#'):
        hex_color = color_str[1:]
        try:
            if len(hex_color) == 3:
                # Short form: #RGB -> #RRGGBB
                r = int(hex_color[0] * 2, 16)
                g = int(hex_color[1] * 2, 16)
                b = int(hex_color[2] * 2, 16)
            elif len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
            else:
                return None
            return RGBColor(r, g, b)
        except ValueError:
            return None
    
    # RGB format: rgb(255, 0, 0)
    rgb_match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str)
    if rgb_match:
        try:
            r = int(rgb_match.group(1))
            g = int(rgb_match.group(2))
            b = int(rgb_match.group(3))
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                return RGBColor(r, g, b)
        except ValueError:
            pass
    
    return None


def set_run_font(run, font_list, size_pt, bold=False, color=None):
    """Set font for a run with fallback support.
    
    Args:
        run: The run to format
        font_list: List of font names (first available will be used)
        size_pt: Font size in points
        bold: Whether to make text bold
        color: RGBColor object or None for default (black)
    """
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    
    # Set color if specified
    if color is not None:
        run.font.color.rgb = color
    
    # Set font name (use first available)
    font_name = font_list[0]
    run.font.name = font_name
    
    # Set East Asian font (required for Chinese characters)
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:eastAsia'), font_name)


def set_paragraph_format(paragraph, line_spacing_pt, first_line_indent_chars=0, alignment=None):
    """Set paragraph formatting."""
    pf = paragraph.paragraph_format
    
    # Line spacing
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(line_spacing_pt)
    
    # Space before/after
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    
    # First line indent (in characters, convert to points: 1 char ≈ font size)
    if first_line_indent_chars > 0:
        pf.first_line_indent = Pt(SIZE_BODY * first_line_indent_chars)
    
    # Alignment
    if alignment:
        pf.alignment = alignment


def set_outline_level(paragraph, level):
    """Set paragraph outline level for navigation pane visibility.
    
    Args:
        paragraph: The paragraph to set outline level for
        level: Outline level (0=Level1, 1=Level2, 2=Level3, etc.)
    """
    pPr = paragraph._p.get_or_add_pPr()
    outlineLvl = OxmlElement('w:outlineLvl')
    outlineLvl.set(qn('w:val'), str(level))
    pPr.append(outlineLvl)


def setup_styles(doc):
    """Configure document styles to match official document formatting (公文格式)."""
    styles = doc.styles
    
    # Helper to set East Asian font on a style
    def set_style_east_asian_font(style, font_name):
        rPr = style.element.get_or_add_rPr()
        rFonts = rPr.get_or_add_rFonts()
        rFonts.set(qn('w:eastAsia'), font_name)
    
    # Helper to clear all paragraph borders (removes default bottom border on Title, etc.)
    def clear_paragraph_borders(style):
        pPr = style.element.get_or_add_pPr()
        # Remove any existing pBdr element
        for pBdr in pPr.findall(qn('w:pBdr')):
            pPr.remove(pBdr)
        # Add empty pBdr with explicit 'none' borders to override inherited borders
        pBdr = OxmlElement('w:pBdr')
        for border_name in ['top', 'left', 'bottom', 'right', 'between']:
            border_el = OxmlElement(f'w:{border_name}')
            border_el.set(qn('w:val'), 'none')
            border_el.set(qn('w:sz'), '0')
            border_el.set(qn('w:space'), '0')
            border_el.set(qn('w:color'), 'auto')
            pBdr.append(border_el)
        pPr.append(pBdr)
    
    # ---- Title Style (文档标题) ----
    try:
        title_style = styles['Title']
    except KeyError:
        title_style = styles.add_style('Title', WD_STYLE_TYPE.PARAGRAPH)
    
    title_style.font.name = FONTS['title'][0]
    set_style_east_asian_font(title_style, FONTS['title'][0])
    title_style.font.size = Pt(SIZE_TITLE)
    title_style.font.bold = False
    title_style.font.color.rgb = RGBColor(0, 0, 0)  # Explicit black color
    title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    title_style.paragraph_format.line_spacing = Pt(LINE_SPACING_TITLE)
    title_style.paragraph_format.space_before = Pt(0)
    title_style.paragraph_format.space_after = Pt(0)
    clear_paragraph_borders(title_style)  # Remove default bottom border line
    
    # ---- Heading 1 Style (一级标题: 黑体 三号) ----
    try:
        h1_style = styles['Heading 1']
    except KeyError:
        h1_style = styles.add_style('Heading 1', WD_STYLE_TYPE.PARAGRAPH)
    
    h1_style.font.name = FONTS['h1'][0]
    set_style_east_asian_font(h1_style, FONTS['h1'][0])
    h1_style.font.size = Pt(SIZE_BODY)
    h1_style.font.bold = False
    h1_style.font.color.rgb = RGBColor(0, 0, 0)  # Explicit black color
    h1_style.paragraph_format.first_line_indent = Pt(SIZE_BODY * 2)
    h1_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    h1_style.paragraph_format.line_spacing = Pt(LINE_SPACING_BODY)
    h1_style.paragraph_format.space_before = Pt(0)
    h1_style.paragraph_format.space_after = Pt(0)
    
    # ---- Heading 2 Style (二级标题: 楷体 三号) ----
    try:
        h2_style = styles['Heading 2']
    except KeyError:
        h2_style = styles.add_style('Heading 2', WD_STYLE_TYPE.PARAGRAPH)
    
    h2_style.font.name = FONTS['h2'][0]
    set_style_east_asian_font(h2_style, FONTS['h2'][0])
    h2_style.font.size = Pt(SIZE_BODY)
    h2_style.font.bold = False
    h2_style.font.color.rgb = RGBColor(0, 0, 0)  # Explicit black color
    h2_style.paragraph_format.first_line_indent = Pt(SIZE_BODY * 2)
    h2_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    h2_style.paragraph_format.line_spacing = Pt(LINE_SPACING_BODY)
    h2_style.paragraph_format.space_before = Pt(0)
    h2_style.paragraph_format.space_after = Pt(0)
    
    # ---- Heading 3 Style (三级标题: 仿宋 三号 加粗) ----
    try:
        h3_style = styles['Heading 3']
    except KeyError:
        h3_style = styles.add_style('Heading 3', WD_STYLE_TYPE.PARAGRAPH)
    
    h3_style.font.name = FONTS['h3'][0]
    set_style_east_asian_font(h3_style, FONTS['h3'][0])
    h3_style.font.size = Pt(SIZE_BODY)
    h3_style.font.bold = True
    h3_style.font.color.rgb = RGBColor(0, 0, 0)  # Explicit black color
    h3_style.paragraph_format.first_line_indent = Pt(SIZE_BODY * 2)
    h3_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    h3_style.paragraph_format.line_spacing = Pt(LINE_SPACING_BODY)
    h3_style.paragraph_format.space_before = Pt(0)
    h3_style.paragraph_format.space_after = Pt(0)
    
    # ---- Normal/Body Style (正文: 仿宋 三号 首行缩进2字符) ----
    normal_style = styles['Normal']
    normal_style.font.name = FONTS['body'][0]
    set_style_east_asian_font(normal_style, FONTS['body'][0])
    normal_style.font.size = Pt(SIZE_BODY)
    normal_style.font.bold = False
    normal_style.paragraph_format.first_line_indent = Pt(SIZE_BODY * 2)
    normal_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    normal_style.paragraph_format.line_spacing = Pt(LINE_SPACING_BODY)
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.space_after = Pt(0)


def setup_page_layout(doc):
    """Set up page layout according to official document standards."""
    section = doc.sections[0]
    
    # Page size: A4
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    
    # Margins
    section.top_margin = Cm(MARGIN_TOP)
    section.bottom_margin = Cm(MARGIN_BOTTOM)
    section.left_margin = Cm(MARGIN_LEFT)
    section.right_margin = Cm(MARGIN_RIGHT)
    
    # Header/Footer distance
    section.header_distance = Cm(HEADER_DISTANCE)
    section.footer_distance = Cm(FOOTER_DISTANCE)


def _clear_paragraph_indent(paragraph):
    """Remove any inherited indent (the Normal style carries a 2-char first-line indent).

    Footer paragraphs inherit from Normal, so without this the left-aligned
    even-page page number would be pushed in by two characters.
    """
    pf = paragraph.paragraph_format
    pf.first_line_indent = Pt(0)
    pf.left_indent = Pt(0)
    pf.right_indent = Pt(0)


def add_page_numbers(doc):
    """Add page numbers in format '- 1 -' at footer with different alignment for odd/even pages."""
    section = doc.sections[0]
    
    # Enable different odd/even headers/footers
    section.different_first_page_header_footer = False
    doc.settings.odd_and_even_pages_header_footer = True
    
    # --- Odd page footer (right aligned) ---
    footer_odd = section.footer
    footer_odd.is_linked_to_previous = False
    
    p_odd = footer_odd.paragraphs[0] if footer_odd.paragraphs else footer_odd.add_paragraph()
    p_odd.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _clear_paragraph_indent(p_odd)
    
    # Add page number content for odd pages
    run1 = p_odd.add_run("- ")
    set_run_font(run1, FONTS['page_num'], SIZE_PAGE_NUM)
    
    # Page number field
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.text = "PAGE"
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    
    run2 = p_odd.add_run()
    run2._r.append(fldChar1)
    run2._r.append(instrText)
    run2._r.append(fldChar2)
    set_run_font(run2, FONTS['page_num'], SIZE_PAGE_NUM)
    
    run3 = p_odd.add_run(" -")
    set_run_font(run3, FONTS['page_num'], SIZE_PAGE_NUM)
    
    # --- Even page footer (left aligned) ---
    footer_even = section.even_page_footer
    footer_even.is_linked_to_previous = False
    
    p_even = footer_even.paragraphs[0] if footer_even.paragraphs else footer_even.add_paragraph()
    p_even.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _clear_paragraph_indent(p_even)
    
    # Add page number content for even pages
    run1e = p_even.add_run("- ")
    set_run_font(run1e, FONTS['page_num'], SIZE_PAGE_NUM)
    
    # Page number field
    fldChar1e = OxmlElement('w:fldChar')
    fldChar1e.set(qn('w:fldCharType'), 'begin')
    instrTexte = OxmlElement('w:instrText')
    instrTexte.text = "PAGE"
    fldChar2e = OxmlElement('w:fldChar')
    fldChar2e.set(qn('w:fldCharType'), 'end')
    
    run2e = p_even.add_run()
    run2e._r.append(fldChar1e)
    run2e._r.append(instrTexte)
    run2e._r.append(fldChar2e)
    set_run_font(run2e, FONTS['page_num'], SIZE_PAGE_NUM)
    
    run3e = p_even.add_run(" -")
    set_run_font(run3e, FONTS['page_num'], SIZE_PAGE_NUM)


def parse_markdown(content):
    """
    Parse Markdown content into structured elements.
    Returns a list of tuples: (type, content, level)
    Types: 'title', 'h1', 'h2', 'h3', 'paragraph', 'list_item', 'table'
    """
    elements = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Empty line - skip
        if not stripped:
            i += 1
            continue
        
        # Headers
        header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if header_match:
            level = len(header_match.group(1))
            text = header_match.group(2)
            
            if level == 1:
                elements.append(('title', text, 1))
            elif level == 2:
                elements.append(('h1', text, 2))
            elif level == 3:
                elements.append(('h2', text, 3))
            else:
                elements.append(('h3', text, level))
            
            i += 1
            continue
        
        # Table detection - look for lines with | that are table rows
        if '|' in stripped and not stripped.startswith('*') and not stripped.startswith('-'):
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i].strip())
                i += 1
            
            if table_lines:
                elements.append(('table', table_lines, 0))
            continue
        
        # Horizontal rule (---, ***, ___)
        if re.match(r'^[-*_]{3,}$', stripped):
            i += 1
            continue
        
        # List items (unordered: - or *)
        list_match = re.match(r'^[-*]\s+(.+)$', stripped)
        if list_match:
            text = list_match.group(1)
            # Calculate indent level based on leading whitespace
            indent = len(line) - len(line.lstrip())
            level = indent // 2 if indent > 0 else 0
            elements.append(('list_item', text, level))
            i += 1
            continue
        
        # Ordered list items (1. 2. etc)
        ordered_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if ordered_match:
            text = ordered_match.group(2)
            elements.append(('list_item', text, 0))
            i += 1
            continue
        
        # Regular paragraph - single line only (don't merge across lines)
        elements.append(('paragraph', stripped, 0))
        i += 1
    
    return elements


def process_inline_formatting(paragraph, text, font_list, size_pt):
    """Process inline formatting (bold, italic, color) and add runs to paragraph.
    
    Supports:
    - **bold** and *italic* markdown syntax
    - <span style="color:red">colored text</span> HTML syntax
    - Nested formatting (e.g., colored bold text)
    """
    # Convert quotes to Chinese
    text = convert_quotes_to_chinese(text)
    
    # First, process HTML color spans and convert to internal format
    # Pattern: <span style="color:VALUE">content</span> or <span style='color:VALUE'>content</span>
    color_pattern = r'<span\s+style\s*=\s*["\']\s*color\s*:\s*([^"\';]+)[^"\'>]*["\']\s*>(.+?)</span>'
    
    # Build a list of segments: (text, color, bold, italic)
    segments = []
    last_end = 0
    
    for color_match in re.finditer(color_pattern, text, re.IGNORECASE | re.DOTALL):
        # Add text before this color span
        if color_match.start() > last_end:
            before_text = text[last_end:color_match.start()]
            segments.append((before_text, None))  # No color
        
        # Add colored segment
        color_value = color_match.group(1).strip()
        colored_text = color_match.group(2)
        segments.append((colored_text, parse_color_value(color_value)))
        
        last_end = color_match.end()
    
    # Add remaining text
    if last_end < len(text):
        segments.append((text[last_end:], None))
    
    # If no color spans found, treat entire text as one segment
    if not segments:
        segments = [(text, None)]
    
    # Now process each segment for bold/italic
    bold_italic_pattern = r'(\*\*(.+?)\*\*|\*([^*]+?)\*)'
    
    for segment_text, segment_color in segments:
        if not segment_text:
            continue
        
        # Find bold/italic matches in this segment
        last_bi_end = 0
        has_bi_matches = False
        
        for bi_match in re.finditer(bold_italic_pattern, segment_text):
            has_bi_matches = True
            
            # Add text before match
            if bi_match.start() > last_bi_end:
                run = paragraph.add_run(segment_text[last_bi_end:bi_match.start()])
                set_run_font(run, font_list, size_pt, color=segment_color)
            
            # Add formatted text
            if bi_match.group(2):  # Bold (**text**)
                run = paragraph.add_run(bi_match.group(2))
                set_run_font(run, font_list, size_pt, bold=True, color=segment_color)
            elif bi_match.group(3):  # Italic (*text*)
                run = paragraph.add_run(bi_match.group(3))
                set_run_font(run, font_list, size_pt, color=segment_color)
                run.font.italic = True
            
            last_bi_end = bi_match.end()
        
        # Add remaining text after last bold/italic match
        if has_bi_matches:
            if last_bi_end < len(segment_text):
                run = paragraph.add_run(segment_text[last_bi_end:])
                set_run_font(run, font_list, size_pt, color=segment_color)
        else:
            # No bold/italic - add entire segment as single run
            run = paragraph.add_run(segment_text)
            set_run_font(run, font_list, size_pt, color=segment_color)


def add_heading_text(paragraph, text, font_list, size_pt, bold=False):
    """Add heading text to paragraph without markdown bold/italic formatting.
    
    Headings (Title, H1, H2, H3) will have markdown ** and * markers stripped,
    but can still be made bold via the bold parameter.
    
    Args:
        paragraph: The paragraph to add text to
        text: The heading text (already processed by normalize_heading_text)
        font_list: List of fonts to use
        size_pt: Font size in points
        bold: Whether to make the text bold (for H3)
    """
    # Convert quotes to Chinese (still needed)
    text = convert_quotes_to_chinese(text)
    
    # Add as single run
    run = paragraph.add_run(text)
    set_run_font(run, font_list, size_pt, bold=bold)


def add_table(doc, table_lines):
    """Add a table to the document."""
    # Parse table
    rows = []
    for line in table_lines:
        # Skip separator line (|---|---|)
        if re.match(r'^[\|\s\-:]+$', line):
            continue
        
        # Split by | and clean
        cells = [cell.strip() for cell in line.split('|')]
        # Remove empty first/last elements from |...|
        cells = [c for c in cells if c]
        if cells:
            rows.append(cells)
    
    if not rows:
        return
    
    # Determine number of columns
    num_cols = max(len(row) for row in rows)
    
    # Create table
    table = doc.add_table(rows=len(rows), cols=num_cols)
    table.style = 'Table Grid'
    
    # Fill cells
    for i, row_data in enumerate(rows):
        row = table.rows[i]
        for j, cell_text in enumerate(row_data):
            if j < num_cols:
                cell = row.cells[j]
                # Clear existing content
                cell.text = ''
                p = cell.paragraphs[0]
                process_inline_formatting(p, cell_text, FONTS['body'], SIZE_BODY)
                set_paragraph_format(p, LINE_SPACING_BODY)


def convert_markdown_to_docx(md_path, output_path=None):
    """Convert a Markdown file to Word document with official formatting."""
    print(f"Processing: {md_path}")
    
    # Read Markdown content
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse Markdown
    elements = parse_markdown(content)
    
    # Create document
    doc = Document()
    
    # Setup page layout
    setup_page_layout(doc)
    
    # Setup styles
    setup_styles(doc)
    
    # Add page numbers
    add_page_numbers(doc)
    
    # Process elements
    for elem_type, elem_content, elem_level in elements:
        
        if elem_type == 'title':
            # Document title: 方正小标宋简体, 二号, centered, NO bold/italic, NO period
            p = doc.add_paragraph(style='Title')
            add_heading_text(p, remove_trailing_period(elem_content), FONTS['title'], SIZE_TITLE)
            set_outline_level(p, 0)  # Outline level 0 for title
            # Add empty line after title (using body format)
            empty_p = doc.add_paragraph()
            set_paragraph_format(empty_p, LINE_SPACING_BODY)
            
        elif elem_type == 'h1':
            # 一级标题: 黑体, 三号, NO period at end, NO bold/italic
            p = doc.add_paragraph(style='Heading 1')
            add_heading_text(p, remove_trailing_period(elem_content), FONTS['h1'], SIZE_BODY)
            set_outline_level(p, 1)  # Outline level 1
            
        elif elem_type == 'h2':
            # 二级标题: 楷体, 三号, ensure ends with exactly one period, NO bold/italic
            p = doc.add_paragraph(style='Heading 2')
            add_heading_text(p, ensure_period_ending(elem_content), FONTS['h2'], SIZE_BODY)
            set_outline_level(p, 2)  # Outline level 2
            
        elif elem_type == 'h3':
            # 三级标题: 仿宋, 三号, ensure ends with exactly one period, BOLD
            p = doc.add_paragraph(style='Heading 3')
            add_heading_text(p, ensure_period_ending(elem_content), FONTS['h3'], SIZE_BODY, bold=True)
            set_outline_level(p, 3)  # Outline level 3
            
        elif elem_type == 'paragraph':
            # Normal paragraph: 仿宋, 三号, first line indent 2 chars
            p = doc.add_paragraph(style='Normal')
            process_inline_formatting(p, elem_content, FONTS['body'], SIZE_BODY)
            
        elif elem_type == 'list_item':
            # List item: treat as paragraph with bullet
            p = doc.add_paragraph(style='Normal')
            indent = '  ' * elem_level
            process_inline_formatting(p, f"{indent}• {elem_content}", FONTS['body'], SIZE_BODY)
            
        elif elem_type == 'table':
            add_table(doc, elem_content)
    
    # Determine output path
    if output_path is None:
        output_path = os.path.splitext(md_path)[0] + '.docx'
    
    # Save document
    doc.save(output_path)
    print(f"Created: {output_path}")
    
    return output_path


def detect_heading_level(paragraph):
    """Detect heading level from paragraph style or content.
    
    Returns:
        int: 0=title, 1=h1, 2=h2, 3=h3, -1=body text
    """
    style_name = paragraph.style.name if paragraph.style else ''
    style_name_lower = style_name.lower()
    
    # Check style name
    if style_name in ['Title', '标题']:
        return 0
    elif 'heading 1' in style_name_lower or style_name == '标题 1':
        return 1
    elif 'heading 2' in style_name_lower or style_name == '标题 2':
        return 2
    elif 'heading 3' in style_name_lower or style_name == '标题 3':
        return 3
    elif 'heading 4' in style_name_lower or style_name == '标题 4':
        return 3  # Treat H4+ as H3
    elif 'heading' in style_name_lower:
        return 3  # Other headings as H3
    
    # Check for outline level in XML
    pPr = paragraph._p.pPr
    if pPr is not None:
        outlineLvl = pPr.find(qn('w:outlineLvl'))
        if outlineLvl is not None:
            level = int(outlineLvl.get(qn('w:val')))
            if level <= 3:
                return level
            return 3
    
    return -1  # Body text


def format_existing_docx(docx_path, output_path=None):
    """Apply official document formatting to an existing Word document.
    
    Args:
        docx_path: Path to the existing .docx file
        output_path: Optional output path. If not specified, overwrites the original file.
    
    Returns:
        str: Path to the formatted document
    """
    print(f"Formatting: {docx_path}")
    
    # Open existing document
    doc = Document(docx_path)
    
    # Setup page layout
    setup_page_layout(doc)
    
    # Setup styles
    setup_styles(doc)
    
    # Process each paragraph
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        
        # Detect heading level
        level = detect_heading_level(paragraph)
        
        if level == 0:
            # Title
            paragraph.style = doc.styles['Title']
            set_outline_level(paragraph, 0)
            # Apply font to all runs
            for run in paragraph.runs:
                set_run_font(run, FONTS['title'], SIZE_TITLE)
                
        elif level == 1:
            # Heading 1 (一级标题)
            paragraph.style = doc.styles['Heading 1']
            set_outline_level(paragraph, 1)
            for run in paragraph.runs:
                set_run_font(run, FONTS['h1'], SIZE_BODY)
                
        elif level == 2:
            # Heading 2 (二级标题)
            paragraph.style = doc.styles['Heading 2']
            set_outline_level(paragraph, 2)
            for run in paragraph.runs:
                set_run_font(run, FONTS['h2'], SIZE_BODY)
                
        elif level == 3:
            # Heading 3 (三级标题)
            paragraph.style = doc.styles['Heading 3']
            set_outline_level(paragraph, 3)
            for run in paragraph.runs:
                set_run_font(run, FONTS['h3'], SIZE_BODY, bold=True)
                
        else:
            # Body text (正文)
            paragraph.style = doc.styles['Normal']
            for run in paragraph.runs:
                set_run_font(run, FONTS['body'], SIZE_BODY)
    
    # Add page numbers
    add_page_numbers(doc)
    
    # Determine output path
    if output_path is None:
        # Create a new file with _formatted suffix to avoid overwriting
        base, ext = os.path.splitext(docx_path)
        output_path = f"{base}_formatted{ext}"
    
    # Save document
    doc.save(output_path)
    print(f"Formatted: {output_path}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown files to Word documents or format existing .docx files with 公文格式 (official document formatting)."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Markdown (.md) or Word (.docx) files to process"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (only valid when processing a single file)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="For .docx files, overwrite the original file instead of creating a new one"
    )
    
    args = parser.parse_args()
    
    if args.output and len(args.files) > 1:
        print("Error: --output can only be used with a single input file.")
        return
    
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        if file_path.lower().endswith('.md'):
            # Convert Markdown to Word
            output = args.output if args.output else None
            convert_markdown_to_docx(file_path, output)
        elif file_path.lower().endswith('.docx'):
            # Format existing Word document
            if args.overwrite:
                output = file_path
            else:
                output = args.output if args.output else None
            format_existing_docx(file_path, output)
        else:
            print(f"Unsupported file type: {file_path}")
            print("  Supported types: .md (Markdown), .docx (Word)")


if __name__ == "__main__":
    main()
