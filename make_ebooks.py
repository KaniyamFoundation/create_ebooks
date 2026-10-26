#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FreeTamilEbooks.com Universal Markdown Ebook Generator
======================================================
Generates beautiful, production-ready ebooks in multiple formats:
  - A4 PDF (Print & Desktop reading)
  - 6-Inch PDF (Kindle & Mobile E-reader optimized)
  - EPUB 3 (Standard reflowable ebook)

Supports all genres:
  - Poetry (கவிதைகள்)
  - Fiction / Novels / Short Stories (நாவல் / சிறுகதைகள்)
  - Non-fiction / Essays / Articles (கட்டுரைகள் / வரலாறு)
  - Technical / Programming / Computer Science (தொழில்நுட்பம் / கணினி)
  - Plays / Drama (நாடகம்)
"""

import os
import sys
import re
import shutil
import argparse
import subprocess
import yaml
import markdown
from pygments.formatters import HtmlFormatter

# Determine paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, 'assets')


# ---------------------------------------------------------------------------
# Metadata Management
# ---------------------------------------------------------------------------
def load_metadata(md_path, config_path=None):
    """
    Load metadata from YAML frontmatter in Markdown and/or book-info.yaml.
    Frontmatter and book-info.yaml are merged with sensible defaults.
    """
    meta = {
        'title': 'மின்னூல் தலைப்பு',
        'subtitle': '',
        'slug': 'ebook',
        'author': 'ஆசிரியர் பெயர்',
        'author_email': '',
        'translator': '',
        'translator_email': '',
        'artist': '',
        'artist_email': '',
        'ebook_maker': 'FreeTamilEbooks Team',
        'ebook_maker_email': 'freetamilebooksteam@gmail.com',
        'license': 'Creative Commons Attribution-NonCommercial-ShareAlike (CC BY-NC-SA 4.0)',
        'publisher': 'FreeTamilEbooks.com , கணியம் அறக்கட்டளை',
        'url': 'https://FreeTamilEbooks.com',
        'category': 'பொது',
        'genre': 'auto',
        'cover_image': 'cover.jpg',
        'backcover_image': 'backcover.jpg',
        'logo_image': 'kaniyam-logo.png',
        'lang': 'ta'
    }

    # 1. Check book-info.yaml in the working directory
    cur_dir = os.path.dirname(os.path.abspath(md_path))
    default_cfg = config_path or os.path.join(cur_dir, 'book-info.yaml')
    if os.path.exists(default_cfg):
        try:
            with open(default_cfg, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
                if 'book_title' in cfg and cfg['book_title']:
                    meta['title'] = str(cfg['book_title']).strip()
                if 'book_title_in_english' in cfg and cfg['book_title_in_english']:
                    meta['slug'] = str(cfg['book_title_in_english']).strip().replace(' ', '_').replace('-', '_')
                if 'author' in cfg and cfg['author']:
                    meta['author'] = str(cfg['author']).strip()
                if 'author_mail' in cfg and cfg['author_mail']:
                    meta['author_email'] = str(cfg['author_mail']).strip()
                if 'translator' in cfg and cfg['translator']:
                    meta['translator'] = str(cfg['translator']).strip()
                if 'translator_email' in cfg and cfg['translator_email']:
                    meta['translator_email'] = str(cfg['translator_email']).strip()
                if 'artist' in cfg and cfg['artist']:
                    meta['artist'] = str(cfg['artist']).strip()
                if 'artist_email' in cfg and cfg['artist_email']:
                    meta['artist_email'] = str(cfg['artist_email']).strip()
                if 'ebook_maker' in cfg and cfg['ebook_maker']:
                    meta['ebook_maker'] = str(cfg['ebook_maker']).strip()
                if 'ebook_maker_email' in cfg and cfg['ebook_maker_email']:
                    meta['ebook_maker_email'] = str(cfg['ebook_maker_email']).strip()
                if 'license' in cfg and cfg['license']:
                    meta['license'] = str(cfg['license']).strip()
                if 'category' in cfg and cfg['category']:
                    meta['category'] = str(cfg['category']).strip()
                if 'cover_image' in cfg and cfg['cover_image']:
                    meta['cover_image'] = str(cfg['cover_image']).strip()
        except Exception as e:
            print(f"[Warning] Error reading {default_cfg}: {e}")

    # 2. Extract YAML Frontmatter from the markdown file
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    md_body = content
    if fm_match:
        fm_raw, md_body = fm_match.groups()
        try:
            fm = yaml.safe_load(fm_raw) or {}
            for k, v in fm.items():
                if not v:
                    continue
                k_norm = k.lower().replace('-', '_')
                if k_norm in ('title', 'book_title'):
                    meta['title'] = str(v).strip()
                elif k_norm in ('subtitle', 'book_subtitle'):
                    meta['subtitle'] = str(v).strip()
                elif k_norm in ('slug', 'book_title_in_english'):
                    meta['slug'] = str(v).strip().replace(' ', '_').replace('-', '_')
                elif k_norm in ('author', 'creator'):
                    if isinstance(v, list) and v:
                        first = v[0]
                        meta['author'] = first.get('text', '') if isinstance(first, dict) else str(first)
                    else:
                        meta['author'] = str(v).strip()
                elif k_norm in ('author_email', 'author_mail'):
                    meta['author_email'] = str(v).strip()
                elif k_norm in ('publisher',):
                    meta['publisher'] = str(v).strip()
                elif k_norm in ('rights', 'license'):
                    meta['license'] = str(v).strip()
                elif k_norm in ('category', 'genre'):
                    meta['category'] = str(v).strip()
                    meta['genre'] = str(v).strip()
                elif k_norm in ('cover_image', 'cover'):
                    meta['cover_image'] = str(v).strip()
                elif k_norm in ('backcover_image', 'backcover'):
                    meta['backcover_image'] = str(v).strip()
                elif k_norm in ('url', 'download_url'):
                    meta['url'] = str(v).strip()
                elif k_norm in ('lang', 'language'):
                    meta['lang'] = str(v).strip()
        except Exception as e:
            print(f"[Warning] Error parsing frontmatter: {e}")

    # Fallbacks and normalizations
    if not meta['slug'] or meta['slug'] == 'ebook':
        base = os.path.splitext(os.path.basename(md_path))[0]
        meta['slug'] = base.replace(' ', '_').replace('-', '_')

    if not meta['url'] or meta['url'] == 'https://FreeTamilEbooks.com':
        clean_slug = meta['slug'].replace('_', '-')
        meta['url'] = f"https://FreeTamilEbooks.com/ebooks/{clean_slug}"

    return meta, md_body


# ---------------------------------------------------------------------------
# Genre Detection
# ---------------------------------------------------------------------------
def detect_genre(meta, md_body, explicit_genre='auto'):
    if explicit_genre and explicit_genre != 'auto':
        return explicit_genre.lower()

    cat = (meta.get('category') or '').lower() + ' ' + (meta.get('genre') or '').lower()
    
    # Check category keywords
    if any(k in cat for k in ['கவிதை', 'பாடல்', 'poetry', 'poem', 'verse', 'haiku']):
        return 'poetry'
    if any(k in cat for k in ['நாவல்', 'கதை', 'சிறுகதை', 'புதினம்', 'fiction', 'novel', 'story']):
        return 'fiction'
    if any(k in cat for k in ['கணினி', 'தொழில்நுட்பம்', 'அறிவியல்', 'technical', 'programming', 'code', 'computer']):
        return 'technical'
    if any(k in cat for k in ['நாடகம்', 'drama', 'play', 'script']):
        return 'drama'

    # Content-based heuristic
    code_blocks = len(re.findall(r'```', md_body))
    if code_blocks >= 4:
        return 'technical'

    # Check for poetry verse pattern
    h1_count = len(re.findall(r'^#\s+', md_body, re.MULTILINE))
    stanzas = len(re.findall(r'\n\s*\n', md_body))
    if h1_count > 10 and (stanzas / max(1, h1_count)) >= 2:
        # Check average line length in stanzas
        sample_lines = [l.strip() for l in md_body.split('\n') if l.strip() and not l.startswith('#')]
        if sample_lines:
            avg_len = sum(len(l) for l in sample_lines[:100]) / min(100, len(sample_lines))
            if avg_len < 65:
                return 'poetry'

    return 'nonfiction'


# ---------------------------------------------------------------------------
# Section Parser
# ---------------------------------------------------------------------------
def parse_sections(md_body, genre):
    """
    Parses Markdown body into structured sections:
      - Front matter: Preface, Author Note, Dedication, Acknowledgements
      - Body sections: Chapters, Poems, or Articles
      - Back matter: FreeTamilEbooks & Kaniyam Foundation info
    """
    # Split by level 1 header '# '
    raw_sections = re.split(r'\n(?=# )', md_body)
    
    front_matter = []
    body_sections = []
    back_matter = []

    # Headings to classify
    preface_keywords = ['முன்னுரை', 'அணிந்துரை', 'நானும் இந்த நூலும்', 'preface', 'foreword']
    author_keywords = ['என்னைப் பற்றி', 'ஆசிரியர் பற்றி', 'ஆசிரியர் உரை', 'about the author', 'author bio']
    dedication_keywords = ['சமர்ப்பணம்', 'நினைவுகளாக', 'dedication']
    ack_keywords = ['நன்றியுரை', 'acknowledgement', 'acknowledgments']
    back_keywords = ['freetamilebooks', 'கணியம் அறக்கட்டளை', 'kaniyam foundation', 'நன்கொடை', 'தொலை நோக்கு', 'பணி இலக்கு']
    skip_keywords = ['பின் அட்டைப்படம்', 'அட்டைப்படம்', 'முன் அட்டைப்படம்', 'back cover', 'front cover']

    for raw in raw_sections:
        raw = raw.strip()
        if not raw:
            continue
        lines = raw.split('\n')
        header_line = lines[0].strip()
        if not header_line.startswith('#'):
            # Text before any header
            body_text = raw
            body_sections.append({
                'title': '',
                'raw': body_text,
                'type': 'body'
            })
            continue

        header_title = re.sub(r'^#+\s*', '', header_line).strip()
        content_text = '\n'.join(lines[1:]).strip()

        # Check skip
        if any(sk == header_title.lower() for sk in skip_keywords):
            continue

        h_lower = header_title.lower()

        # Classify
        if any(kw in h_lower for kw in dedication_keywords):
            front_matter.append({'title': header_title, 'type': 'dedication', 'raw': content_text})
        elif any(kw in h_lower for kw in preface_keywords):
            front_matter.append({'title': header_title, 'type': 'preface', 'raw': content_text})
        elif any(kw in h_lower for kw in author_keywords):
            front_matter.append({'title': header_title, 'type': 'author_note', 'raw': content_text})
        elif any(kw in h_lower for kw in ack_keywords):
            front_matter.append({'title': header_title, 'type': 'acknowledgement', 'raw': content_text})
        elif any(kw in h_lower for kw in back_keywords):
            back_matter.append({'title': header_title, 'raw': content_text})
        else:
            body_sections.append({
                'title': header_title,
                'raw': content_text,
                'type': 'body'
            })

    # If all sections ended up in front matter, migrate non-dedication sections to body
    if not body_sections and front_matter:
        new_fm = []
        for fm in front_matter:
            if fm.get('type') == 'dedication':
                new_fm.append(fm)
            else:
                body_sections.append({'title': fm['title'], 'raw': fm['raw'], 'type': 'body'})
        front_matter = new_fm

    return front_matter, body_sections, back_matter


# ---------------------------------------------------------------------------
# Section Formatter by Genre
# ---------------------------------------------------------------------------
md_converter = markdown.Markdown(extensions=[
    'extra',
    'codehilite',
    'tables',
    'fenced_code',
    'footnotes',
    'def_list',
    'attr_list'
])

def format_body_section(sec, genre, index):
    title = sec['title']
    raw_content = sec['raw']
    sec_id = f"section-{index}"

    if genre == 'poetry':
        # Split into stanzas separated by blank lines
        raw_stanzas = re.split(r'\n\s*\n', raw_content)
        stanzas_html = []
        for rs in raw_stanzas:
            lines = [l.strip() for l in rs.split('\n') if l.strip()]
            if not lines:
                continue
            lines_html = []
            for l in lines:
                # Remove orphan HTML tags
                c = re.sub(r'</?(div|span|p)[^>]*>', '', l)
                c = re.sub(r'<br\s*/?>', '', c).strip()
                if c and c != '❦':
                    # Support inline bold/italic
                    c_md = markdown.markdown(c).strip()
                    if c_md.startswith('<p>') and c_md.endswith('</p>'):
                        c_md = c_md[3:-4]
                    lines_html.append(f'<p class="poem-line">{c_md}</p>')
            if lines_html:
                stanzas_html.append('<div class="stanza">\n' + '\n'.join(lines_html) + '\n</div>')

        stanzas_joined = '\n'.join(stanzas_html)
        return f'''
        <div class="section-page poem-page" id="{sec_id}">
          <h2 class="poem-title">{title}</h2>
          <div class="ornament">❦</div>
          <div class="poem-body">
            {stanzas_joined}
          </div>
        </div>'''

    elif genre == 'fiction':
        # Novels / short stories: scene breaks, first paragraph flush left
        html_content = md_converter.convert(raw_content)
        # Transform <hr /> to scene break ornaments
        html_content = re.sub(r'<hr\s*/?>', '<div class="scene-break ornament">❦</div>', html_content)
        return f'''
        <div class="section-page chapter-page genre-fiction" id="{sec_id}">
          <h1 class="chapter-title">{title}</h1>
          <div class="ornament">❦</div>
          <div class="chapter-body">
            {html_content}
          </div>
        </div>'''

    elif genre == 'technical':
        # Technical / computer: code blocks, tables, callouts
        html_content = md_converter.convert(raw_content)
        # Wrap blockquotes containing 'Note:' or 'குறிப்பு:' in styled note boxes
        html_content = re.sub(
            r'<blockquote>\s*<p>(?:<strong>(?:Note|குறிப்பு|முக்கியம்|எச்சரிக்கை)[^<]*</strong>|\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\])(.*?)</p>\s*</blockquote>',
            r'<div class="callout-box"><div class="callout-title">📌 குறிப்பு</div><p>\1</p></div>',
            html_content, flags=re.DOTALL
        )
        return f'''
        <div class="section-page chapter-page genre-technical" id="{sec_id}">
          <h1 class="chapter-title">{title}</h1>
          <div class="chapter-body">
            {html_content}
          </div>
        </div>'''

    else:
        # Standard non-fiction / essays / articles
        html_content = md_converter.convert(raw_content)
        return f'''
        <div class="section-page chapter-page genre-nonfiction" id="{sec_id}">
          <h1 class="chapter-title">{title}</h1>
          <div class="ornament">❦</div>
          <div class="chapter-body">
            {html_content}
          </div>
        </div>'''


# ---------------------------------------------------------------------------
# Back Matter Formatter
# ---------------------------------------------------------------------------
def format_back_matter(back_matter, assets_dir):
    if not back_matter:
        # Load default back matter if available
        def_bm_file = os.path.join(assets_dir, 'default_backmatter.md')
        if os.path.exists(def_bm_file):
            with open(def_bm_file, 'r', encoding='utf-8') as f:
                def_bm_text = f.read()
            raw_sections = re.split(r'\n(?=# )', def_bm_text)
            for r in raw_sections:
                r = r.strip()
                if not r:
                    continue
                lines = r.split('\n')
                h = lines[0].lstrip('# ').strip()
                back_matter.append({'title': h, 'raw': '\n'.join(lines[1:]).strip()})

    out = []
    in_donation = False

    for bm in back_matter:
        h = bm['title']
        raw = bm['raw']
        lines = [l.strip() for l in raw.split('\n') if l.strip()]

        if 'FreeTamilEbooks' in h:
            out.append('<div class="back-section page-break">')
            out.append(f'<h1 class="bm-title">{h}</h1>')
            out.append('<div class="ornament">❦</div>')
        elif 'கணியம் அறக்கட்டளை' in h or 'Kaniyam' in h:
            if in_donation:
                out.append('</div>')
                in_donation = False
            out.append('</div>')
            out.append('<div class="back-section page-break">')
            out.append('<div class="logo-box"><img src="kaniyam-logo.png" alt="Kaniyam Foundation" class="kaniyam-logo"></div>')
            out.append(f'<h1 class="bm-title">{h}</h1>')
            out.append('<div class="ornament">❦</div>')
        else:
            out.append(f'<h2 class="bm-heading">{h}</h2>')

        in_list = False
        for l in lines:
            if l.startswith('##'):
                if in_list:
                    out.append('</ul>')
                    in_list = False
                h2_text = re.sub(r'^##\s*', '', l).strip()
                if 'நன்கொடை' in h2_text or 'Donation' in h2_text:
                    if in_donation:
                        out.append('</div>')
                    out.append('<div class="donation-card">')
                    out.append(f'<h2 class="bm-heading" style="margin-top:0;">{h2_text}</h2>')
                    in_donation = True
                else:
                    if in_donation:
                        out.append('</div>')
                        in_donation = False
                    out.append(f'<h2 class="bm-heading">{h2_text}</h2>')
            elif l.startswith('* ') or l.startswith('- '):
                if not in_list:
                    out.append('<ul class="bm-list">')
                    in_list = True
                item_text = l[2:].strip()
                # Markdown link to HTML
                item_html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', item_text)
                out.append(f'<li>{item_html}</li>')
            else:
                if in_list:
                    out.append('</ul>')
                    in_list = False
                if 'kaniyam-logo.png' in l:
                    continue
                if any(k in l for k in ['Account Number', 'Union Bank', 'IFSC', 'UBIN0560618', '606 1010', '606101010050279']):
                    out.append(f'<p class="bank-line">{l}</p>')
                elif (l.endswith(':') or l.endswith('?')) and len(l) < 80:
                    out.append(f'<h3 class="bm-subheading">{l}</h3>')
                else:
                    l_html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', l)
                    out.append(f'<p class="bm-p">{l_html}</p>')

        if in_list:
            out.append('</ul>')

    if in_donation:
        out.append('</div>')
    out.append('</div>')
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# CSS Generators (A4 vs 6-Inch Profiles)
# ---------------------------------------------------------------------------
def generate_css(profile, genre):
    pygments_css = HtmlFormatter(style='friendly').get_style_defs('.codehilite')

    if profile == '6inch':
        page_size = "90mm 120mm"
        margins = "7.5mm 7mm 9.5mm 7mm"
        body_font_size = "8.2pt"
        body_line_height = "1.42"
        h1_font_size = "10.5pt"
        h2_font_size = "9.5pt"
        toc_font_size = "7.6pt"
        is_compact = True
    else: # A4
        page_size = "210mm 297mm"
        margins = "22mm 20mm 24mm 20mm"
        body_font_size = "10.5pt"
        body_line_height = "1.65"
        h1_font_size = "15pt"
        h2_font_size = "12.5pt"
        toc_font_size = "9.8pt"
        is_compact = False

    header_running = """
  @top-left {
    content: string(book-title);
    font-family: "Noto Serif Tamil", serif;
    font-size: 8pt;
    color: #888888;
  }
  @top-right {
    content: string(chapter-title);
    font-family: "Noto Serif Tamil", serif;
    font-size: 8pt;
    color: #888888;
  }
""" if not is_compact else ""

    css = f'''
@charset "utf-8";

@page {{
  size: {page_size};
  margin: {margins};
  {header_running}
  @bottom-center {{
    content: counter(page);
    font-family: "Noto Serif Tamil", "Mukta Malar", serif;
    font-size: {"7.5pt" if is_compact else "9pt"};
    color: #888888;
  }}
}}

@page:first {{
  margin: 0;
  @top-left {{ content: none; }}
  @top-right {{ content: none; }}
  @bottom-center {{ content: none; }}
}}

@page blank-page {{
  margin: {margins};
  @top-left {{ content: none; }}
  @top-right {{ content: none; }}
  @bottom-center {{ content: none; }}
}}

@page fullbleed-back {{
  margin: 0;
  @top-left {{ content: none; }}
  @top-right {{ content: none; }}
  @bottom-center {{ content: none; }}
}}

.no-page-num {{
  page: blank-page;
}}

.back-cover-page {{
  page: fullbleed-back;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}}

body {{
  font-family: "Noto Serif Tamil", "Mukta Malar", "Lohit Tamil", serif;
  font-size: {body_font_size};
  line-height: {body_line_height};
  color: #1a1a1a;
  margin: 0;
  padding: 0;
  text-rendering: optimizeLegibility;
}}

.page-break {{
  page-break-before: always;
  break-before: page;
}}

.cover-page {{
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  page-break-after: always;
}}

.cover-img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}

/* Half-title */
.half-title-page {{
  page-break-before: always;
  text-align: center;
  padding-top: {"22mm" if is_compact else "60mm"};
}}

.half-title {{
  font-family: "Noto Sans Tamil", "Mukta Malar", sans-serif;
  font-size: {"12pt" if is_compact else "22pt"};
  font-weight: 700;
  color: #5c1d24;
  margin-bottom: 2mm;
  string-set: book-title content();
}}

.half-subtitle {{
  font-size: {"7.8pt" if is_compact else "12pt"};
  color: #555555;
  font-style: italic;
  margin-bottom: 4mm;
}}

.half-author {{
  font-size: {"9pt" if is_compact else "14pt"};
  color: #333333;
  margin-top: 4mm;
}}

.ornament {{
  text-align: center;
  color: #bfa15f;
  font-size: {"8pt" if is_compact else "11pt"};
  margin-bottom: 2mm;
}}

/* Colophon */
.colophon-page {{
  page-break-before: always;
  padding-top: {"2mm" if is_compact else "15mm"};
}}

.colophon-title {{
  font-size: {"10pt" if is_compact else "15pt"};
  font-weight: 700;
  color: #5c1d24;
  text-align: center;
  margin-bottom: 1.5mm;
}}

.colophon-box {{
  border: 1pt solid #d4c8b8;
  background-color: #faf8f5;
  padding: {"2.5mm 3.5mm" if is_compact else "6mm 8mm"};
  border-radius: 2mm;
  font-size: {"7.2pt" if is_compact else "9.8pt"};
  line-height: 1.35;
}}

.colophon-line {{
  margin: 0.8mm 0;
}}

.colophon-label {{
  font-weight: 700;
  color: #4a2227;
}}

.colophon-logo-box {{
  text-align: center;
  margin-top: {"2mm" if is_compact else "6mm"};
}}

.colophon-logo {{
  max-width: {"32mm" if is_compact else "55mm"};
  height: auto;
}}

/* Front Matter */
.section-page {{
  page-break-before: always;
  break-inside: avoid;
}}

.section-title, .chapter-title {{
  font-family: "Noto Sans Tamil", "Mukta Malar", sans-serif;
  font-size: {h1_font_size};
  font-weight: 700;
  color: #5c1d24;
  text-align: center;
  margin: 0 0 1.5mm 0;
  string-set: chapter-title content();
}}

.prose-p {{
  font-size: {"7.3pt" if is_compact else "10.2pt"};
  line-height: {"1.30" if is_compact else "1.65"};
  margin: 0 0 1.5mm 0;
  text-align: justify;
}}

.dedication-page {{
  page-break-before: always;
  text-align: center;
  padding-top: {"18mm" if is_compact else "50mm"};
}}

.dedication-line {{
  font-size: {"8.5pt" if is_compact else "12.5pt"};
  line-height: 1.55;
  color: #444444;
  margin: 1.5mm 0;
}}

/* Table of Contents */
.toc-page {{
  page-break-before: always;
}}

.toc-heading {{
  font-size: {h1_font_size};
  font-weight: 700;
  color: #5c1d24;
  text-align: center;
  margin-bottom: 2mm;
}}

table.toc-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: {toc_font_size};
  line-height: {"1.2" if is_compact else "1.4"};
}}

td.toc-name {{
  white-space: nowrap;
  padding: {"0.9mm 0" if is_compact else "1.5mm 0"};
}}

td.toc-name a {{
  text-decoration: none;
  color: #222222;
}}

td.toc-dots {{
  width: 100%;
  border-bottom: 1px dotted #aaaaaa;
  position: relative;
  top: -3px;
}}

td.toc-num {{
  white-space: nowrap;
  text-align: right;
  padding-left: 2mm;
}}

td.toc-num a {{
  text-decoration: none;
  color: #666666;
}}

td.toc-num a::after {{
  content: target-counter(attr(href, url), page);
}}

/* Poetry Stanzas */
.poem-page {{
  page-break-before: always;
  padding-top: {"1mm" if is_compact else "10mm"};
}}

.poem-title {{
  font-size: {h1_font_size};
  font-weight: 700;
  color: #5c1d24;
  text-align: center;
  margin: 0 0 1mm 0;
  string-set: chapter-title content();
}}

.poem-body {{
  text-align: center;
}}

.stanza {{
  break-inside: avoid;
  page-break-inside: avoid;
  display: inline-block;
  text-align: left;
  margin-bottom: {"2.5mm" if is_compact else "5mm"};
}}

.poem-line {{
  font-size: {"8.2pt" if is_compact else "10.5pt"};
  line-height: {"1.42" if is_compact else "1.65"};
  margin: 0;
  padding: 0;
  color: #1a1a1a;
}}

/* Fiction / Novels */
.genre-fiction p {{
  text-indent: 1.8em;
  margin: 0;
  margin-bottom: 0.2em;
  text-align: justify;
  line-height: {"1.42" if is_compact else "1.65"};
}}

.genre-fiction .first-p,
.genre-fiction h1 + p,
.genre-fiction h2 + p {{
  text-indent: 0;
}}

.scene-break {{
  text-align: center;
  margin: 1.2em 0;
}}

/* Nonfiction & Technical */
.genre-nonfiction p, .genre-technical p {{
  text-indent: 0;
  margin-top: 0;
  margin-bottom: 0.8em;
  text-align: justify;
}}

blockquote {{
  margin: 1em 0;
  padding: 0.5em 0.8em;
  border-left: 3px solid #8c2d19;
  background-color: #fbf8f5;
  font-style: italic;
}}

.callout-box {{
  border: 1pt solid #2b6cb0;
  background-color: #ebf8ff;
  border-left: 3pt solid #2b6cb0;
  padding: 0.6em 0.8em;
  margin: 1em 0;
  border-radius: 2px;
  break-inside: avoid;
}}

.callout-title {{
  font-weight: bold;
  color: #2b6cb0;
  margin-bottom: 0.3em;
}}

/* Code Blocks */
pre {{
  background-color: #f6f8fa;
  border: 1pt solid #d0d7de;
  border-radius: 2mm;
  padding: {"2mm 3mm" if is_compact else "4mm 6mm"};
  font-family: "DejaVu Sans Mono", monospace;
  font-size: {"7pt" if is_compact else "8.8pt"};
  line-height: 1.35;
  white-space: pre-wrap;
  word-break: break-all;
  overflow-wrap: break-word;
  break-inside: avoid;
}}

code {{
  font-family: "DejaVu Sans Mono", monospace;
  background-color: #f2f2f2;
  padding: 1px 3px;
  border-radius: 2px;
}}

/* Tables */
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
  font-size: {"7.5pt" if is_compact else "9.5pt"};
  break-inside: avoid;
}}

th, td {{
  border: 1pt solid #d4c8b8;
  padding: {"1.5mm 2mm" if is_compact else "3mm 4mm"};
  text-align: left;
}}

th {{
  background-color: #f2ece4;
  font-weight: 700;
  color: #4a2227;
}}

tr:nth-child(even) td {{
  background-color: #faf8f5;
}}

/* Images */
img {{
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1.5em auto;
}}

/* Back Matter */
.back-section {{
  page-break-before: always;
}}

.bm-title {{
  font-size: {h1_font_size};
  font-weight: 700;
  color: #5c1d24;
  text-align: center;
  margin: 0 0 1.5mm 0;
}}

.bm-heading {{
  font-size: {h2_font_size};
  font-weight: 700;
  color: #4a2227;
  margin: {"2.5mm 0 1mm 0" if is_compact else "5mm 0 2mm 0"};
}}

.bm-subheading {{
  font-size: {"7.6pt" if is_compact else "10pt"};
  font-weight: 700;
  color: #333333;
  margin: 1.5mm 0 0.8mm 0;
}}

.bm-p {{
  font-size: {"7.2pt" if is_compact else "9.8pt"};
  line-height: {"1.30" if is_compact else "1.6"};
  margin: 0 0 1.2mm 0;
  text-align: justify;
}}

.bm-list {{
  margin: 0 0 1.5mm 0;
  padding-left: 4mm;
}}

.bm-list li {{
  font-size: {"7.2pt" if is_compact else "9.8pt"};
  margin-bottom: 0.8mm;
}}

.logo-box {{
  text-align: center;
  margin: 2mm 0;
}}

.kaniyam-logo {{
  max-width: {"35mm" if is_compact else "55mm"};
  height: auto;
}}

.donation-card {{
  break-inside: avoid;
  border: 1pt solid #d4c8b8;
  background-color: #faf8f5;
  border-radius: 2mm;
  padding: {"2.5mm 3.5mm" if is_compact else "5mm 7mm"};
  margin-top: 2.5mm;
}}

.bank-line {{
  font-family: monospace, "Noto Serif Tamil";
  font-size: {"7.5pt" if is_compact else "10pt"};
  margin: 0.8mm 0;
  color: #111111;
}}

{pygments_css}
'''
    return css


# ---------------------------------------------------------------------------
# HTML Document Builder
# ---------------------------------------------------------------------------
def build_html(meta, front_matter, body_sections, back_matter, genre, profile, working_dir):
    css_content = generate_css(profile, genre)

    # 1. Front Cover Page
    cover_html = ""
    cover_file = meta.get('cover_image') or 'cover.jpg'
    if os.path.exists(os.path.join(working_dir, cover_file)):
        cover_html = f'''
<div class="cover-page">
  <img src="{cover_file}" class="cover-img" alt="Front Cover">
</div>'''

    # 2. Half-Title Page
    subtitle_div = f'<div class="half-subtitle">{meta["subtitle"]}</div>' if meta.get('subtitle') else ''
    half_title_html = f'''
<div class="half-title-page no-page-num">
  <div class="half-title">{meta['title']}</div>
  <div class="ornament">❦</div>
  {subtitle_div}
  <div class="half-author">{meta['author']}</div>
</div>'''

    # 3. Colophon Page
    author_mail_str = f" ({meta['author_email']})" if meta.get('author_email') else ""
    artist_str = meta.get('artist') or meta.get('ebook_maker')
    artist_mail_str = f" ({meta.get('artist_email') or meta.get('ebook_maker_email')})" if (meta.get('artist_email') or meta.get('ebook_maker_email')) else ""
    translator_line = f'<div class="colophon-line"><span class="colophon-label">மொழிபெயர்ப்பாளர்:</span> {meta["translator"]}</div>' if meta.get('translator') else ''

    logo_path = 'kaniyam-logo.png'
    logo_html = ''
    if os.path.exists(os.path.join(working_dir, logo_path)):
        logo_html = f'<div class="colophon-logo-box"><img src="{logo_path}" class="colophon-logo" alt="Kaniyam Foundation"></div>'

    colophon_html = f'''
<div class="colophon-page no-page-num">
  <div class="colophon-title">{meta['title']}</div>
  <div class="ornament">❦</div>
  <div class="colophon-box">
    <div class="colophon-line"><span class="colophon-label">மின்னூல் பெயர்:</span> {meta['title']}</div>
    <div class="colophon-line"><span class="colophon-label">வகை:</span> {meta['category']}</div>
    <div class="colophon-line"><span class="colophon-label">ஆசிரியர்:</span> {meta['author']}{author_mail_str}</div>
    {translator_line}
    <div class="colophon-line"><span class="colophon-label">அட்டைப்படம், மின்னூலாக்கம்:</span> {artist_str}{artist_mail_str}</div>
    <div class="colophon-line"><span class="colophon-label">காப்புரிமை:</span> {meta['license']}</div>
    <div class="colophon-line"><span class="colophon-label">வெளியீடு:</span> {meta['publisher']}</div>
    <div class="colophon-line"><span class="colophon-label">பதிவிறக்கம்:</span> <a href="{meta['url']}">{meta['url']}</a></div>
  </div>
  {logo_html}
</div>'''

    # 4. Front Matter Sections (Preface, Author Note, Dedication)
    fm_html_blocks = []
    for fm in front_matter:
        t = fm['title']
        raw = fm['raw']
        fm_type = fm.get('type')

        if fm_type == 'dedication':
            lines = [l.strip() for l in raw.split('\n') if l.strip()]
            d_lines = ''.join([f'<p class="dedication-line">{l.rstrip(r"\\")}</p>' for l in lines])
            fm_html_blocks.append(f'''
<div class="dedication-page">
  <div class="ornament" style="margin-bottom: 8mm;">❦</div>
  {d_lines}
  <div class="ornament" style="margin-top: 8mm;">❦</div>
</div>''')
        else:
            p_html = md_converter.convert(raw)
            fm_html_blocks.append(f'''
<div class="section-page">
  <h2 class="section-title">{t}</h2>
  <div class="ornament">❦</div>
  <div class="prose-body">
    {p_html}
  </div>
</div>''')

    # 5. Table of Contents (TOC)
    toc_rows = []
    for idx, sec in enumerate(body_sections, 1):
        if not sec['title']:
            continue
        sec_id = f"section-{idx}"
        toc_rows.append(f'''
        <tr>
          <td class="toc-name"><a href="#{sec_id}">{sec['title']}</a></td>
          <td class="toc-dots"></td>
          <td class="toc-num"><a href="#{sec_id}"></a></td>
        </tr>''')

    toc_html = ""
    if toc_rows:
        toc_html = f'''
<div class="toc-page">
  <div class="toc-heading">பொருளடக்கம்</div>
  <div class="ornament">❦</div>
  <table class="toc-table">
    {''.join(toc_rows)}
  </table>
</div>'''

    # 6. Main Body Sections
    body_html_blocks = []
    for idx, sec in enumerate(body_sections, 1):
        body_html_blocks.append(format_body_section(sec, genre, idx))

    # 7. Back Matter
    back_matter_rendered = format_back_matter(back_matter, ASSETS_DIR)

    # 8. Back Cover Page
    backcover_html = ""
    backcover_file = meta.get('backcover_image') or 'backcover.jpg'
    if os.path.exists(os.path.join(working_dir, backcover_file)):
        backcover_html = f'''
<div class="back-cover-page page-break">
  <img src="{backcover_file}" class="cover-img" alt="Back Cover">
</div>'''

    full_html = f'''<!DOCTYPE html>
<html lang="{meta.get('lang', 'ta')}">
<head>
<meta charset="utf-8">
<title>{meta['title']} ({profile.upper()})</title>
<style>
{css_content}
</style>
</head>
<body>

{cover_html}
{half_title_html}
{colophon_html}
{''.join(fm_html_blocks)}
{toc_html}
{''.join(body_html_blocks)}
{back_matter_rendered}
{backcover_html}

</body>
</html>'''

    return full_html


# ---------------------------------------------------------------------------
# EPUB Generator via Pandoc
# ---------------------------------------------------------------------------
def generate_epub(md_path, meta, genre, working_dir, output_epub):
    cover_file = meta.get('cover_image') or 'cover.jpg'
    cover_arg = []
    if os.path.exists(os.path.join(working_dir, cover_file)):
        cover_arg = [f'--epub-cover-image={cover_file}']

    # Choose stylesheet
    css_file = 'epub_style.css'
    if not os.path.exists(os.path.join(working_dir, css_file)):
        # Copy from assets
        asset_css = os.path.join(ASSETS_DIR, 'epub_style.css')
        if os.path.exists(asset_css):
            shutil.copyfile(asset_css, os.path.join(working_dir, css_file))

    css_arg = [f'--css={css_file}'] if os.path.exists(os.path.join(working_dir, css_file)) else []

    from_arg = '--from=markdown+hard_line_breaks' if genre == 'poetry' else '--from=markdown'

    cmd = [
        'pandoc',
        md_path,
        '-o', output_epub,
        from_arg,
        '--toc',
        '--toc-depth=2',
        f'--metadata=title:{meta["title"]}',
        f'--metadata=author:{meta["author"]}',
        f'--metadata=lang:{meta.get("lang", "ta")}',
        f'--metadata=publisher:{meta["publisher"]}',
        f'--metadata=rights:{meta["license"]}'
    ] + cover_arg + css_arg

    print(f"Running pandoc to generate EPUB: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=working_dir, check=True)


# ---------------------------------------------------------------------------
# Upload Package Preparer
# ---------------------------------------------------------------------------
def prepare_upload_dir(meta, working_dir, a4_pdf, six_inch_pdf, epub_file):
    slug = meta['slug']
    upload_dir_name = f"{slug}-upload"
    upload_dir = os.path.join(working_dir, upload_dir_name)
    os.makedirs(upload_dir, exist_ok=True)

    # Copy core generated books
    for f in [a4_pdf, six_inch_pdf, epub_file]:
        if os.path.exists(os.path.join(working_dir, f)):
            shutil.copyfile(os.path.join(working_dir, f), os.path.join(upload_dir, f))

    # Copy cover, backcover, config, rules, pictures
    for extra in ['cover.jpg', 'backcover.jpg', 'book-info.yaml', '_rules.conf', 'Pictures.zip']:
        src = os.path.join(working_dir, extra)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(upload_dir, extra))
        elif extra == '_rules.conf':
            # Copy from assets if not in working_dir
            asset_rules = os.path.join(ASSETS_DIR, '_rules.conf')
            if os.path.exists(asset_rules):
                shutil.copyfile(asset_rules, os.path.join(upload_dir, extra))

    print(f"\n[Packaging] Prepared upload folder at: {upload_dir_name}/")
    print(f"[Internet Archive] Upload command:")
    print(f"  ia upload {slug}-$(date +%Y-%m-%d-%H-%M-%S) -m collection:opensource -m mediatype:texts -m sponsor:FreeTamilEbooks -m language:tam {upload_dir_name}/*\n")


# ---------------------------------------------------------------------------
# Main CLI Function
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="FreeTamilEbooks.com Universal Ebook Generator (Markdown -> A4 PDF, 6-Inch PDF, EPUB)"
    )
    parser.add_argument('input', nargs='?', default=None, help="Path to input Markdown file (auto-detects if omitted)")
    parser.add_argument('-c', '--config', default=None, help="Path to YAML config (default: book-info.yaml)")
    parser.add_argument('-g', '--genre', default='auto', choices=['auto', 'poetry', 'fiction', 'technical', 'drama', 'nonfiction'], help="Genre profile")
    parser.add_argument('-f', '--formats', default='all', choices=['all', 'pdf', 'a4', '6inch', 'epub'], help="Formats to compile")
    parser.add_argument('--no-upload', action='store_true', help="Skip preparing <slug>-upload directory")
    args = parser.parse_args()

    # Determine input markdown file
    cur_dir = os.getcwd()
    md_file = args.input
    if not md_file:
        candidates = [f for f in os.listdir(cur_dir) if f.endswith('.md') and not f.startswith('README') and not 'style_guide' in f]
        if not candidates:
            print("[Error] No Markdown (.md) file found in current directory.")
            sys.exit(1)
        md_file = candidates[0]
        print(f"[Auto-detect] Using markdown file: {md_file}")

    if not os.path.isfile(md_file):
        print(f"[Error] File not found: {md_file}")
        sys.exit(1)

    working_dir = os.path.dirname(os.path.abspath(md_file))

    # Ensure kaniyam-logo.png is present in working dir
    local_logo = os.path.join(working_dir, 'kaniyam-logo.png')
    if not os.path.exists(local_logo):
        asset_logo = os.path.join(ASSETS_DIR, 'kaniyam-logo.png')
        if os.path.exists(asset_logo):
            shutil.copyfile(asset_logo, local_logo)

    # 1. Load Metadata
    meta, md_body = load_metadata(md_file, args.config)
    slug = meta['slug']
    print(f"\n=======================================================")
    print(f"📖 Book Title : {meta['title']}")
    print(f"✍️  Author     : {meta['author']}")
    print(f"🏷️  Slug       : {slug}")
    print(f"📂 Category   : {meta['category']}")

    # 2. Detect Genre
    genre = detect_genre(meta, md_body, args.genre)
    print(f"🎭 Genre Mode : {genre.upper()}")
    print(f"=======================================================\n")

    # 3. Parse Sections
    front_matter, body_sections, back_matter = parse_sections(md_body, genre)
    print(f"Detected: {len(front_matter)} front matter section(s), {len(body_sections)} body chapter(s)/poem(s), {len(back_matter)} back matter block(s)")

    # File names
    a4_html_file = f"{slug}_a4.html"
    a4_pdf_file = f"{slug}_a4.pdf"
    six_inch_html_file = f"{slug}_6_inch.html"
    six_inch_pdf_file = f"{slug}_6_inch.pdf"
    epub_file = f"{slug}.epub"

    # WeasyPrint import
    import weasyprint

    # 4. Compile 6-inch PDF
    if args.formats in ('all', 'pdf', '6inch'):
        print("\n⚙️  Generating 6-inch HTML & PDF...")
        html_6inch = build_html(meta, front_matter, body_sections, back_matter, genre, '6inch', working_dir)
        with open(os.path.join(working_dir, six_inch_html_file), 'w', encoding='utf-8') as f:
            f.write(html_6inch)
        weasyprint.HTML(os.path.join(working_dir, six_inch_html_file)).write_pdf(
            os.path.join(working_dir, six_inch_pdf_file)
        )
        print(f"✅ Created 6-inch PDF: {six_inch_pdf_file}")

    # 5. Compile A4 PDF
    if args.formats in ('all', 'pdf', 'a4'):
        print("\n⚙️  Generating A4 HTML & PDF...")
        html_a4 = build_html(meta, front_matter, body_sections, back_matter, genre, 'a4', working_dir)
        with open(os.path.join(working_dir, a4_html_file), 'w', encoding='utf-8') as f:
            f.write(html_a4)
        weasyprint.HTML(os.path.join(working_dir, a4_html_file)).write_pdf(
            os.path.join(working_dir, a4_pdf_file)
        )
        print(f"✅ Created A4 PDF: {a4_pdf_file}")

    # 6. Compile EPUB
    if args.formats in ('all', 'epub'):
        print("\n⚙️  Generating EPUB via Pandoc...")
        generate_epub(md_file, meta, genre, working_dir, epub_file)
        print(f"✅ Created EPUB: {epub_file}")

    # 7. Prepare Upload Directory
    if not args.no_upload:
        prepare_upload_dir(meta, working_dir, a4_pdf_file, six_inch_pdf_file, epub_file)

    print("🎉 All book generation tasks completed successfully!\n")


if __name__ == '__main__':
    main()
