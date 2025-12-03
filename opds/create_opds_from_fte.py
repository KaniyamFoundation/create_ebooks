#!/usr/bin/env python3
"""
FreeTamilEbooks OPDS Generator (Full)
Fetches books via WordPress REST API, builds OPDS feeds:
- All books: books.opds.xml
- Categories-first: categories.opds.xml
- Category-specific feeds: {slug}.opds.xml
"""
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, urlunsplit
from datetime import datetime, timezone
import uuid
import time
import sys
from collections import defaultdict
import re
import json

# ---------------- CONFIG ----------------
BASE_URL = "https://freetamilebooks.com/wp-json/wp/v2"
OUTPUT_JSON = "books.json"
OUTPUT_OPDS_ALL = "books.opds.xml"
OUTPUT_OPDS_CATEGORIES = "categories.opds.xml"
PER_PAGE = 20
MAX_PAGES = 1000
LIMIT_BOOKS = None
DELAY_INTERVAL = 5
DELAY_SECONDS = 10
PUBLISHER = "FreeTamilEbooks.com by Kaniyam Foundation"
LANGUAGE = "ta"
USER_AGENT = "fte-opds-generator/1.0 (+https://freetamilebooks.com)"
REQUEST_TIMEOUT = 20
# ----------------------------------------

# Namespaces
ATOM_NS = "http://www.w3.org/2005/Atom"
DC_NS = "http://purl.org/dc/elements/1.1/"
ET.register_namespace("", ATOM_NS)
ET.register_namespace("dc", DC_NS)

HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}

# ---------------- UTILS ----------------
def fetch_json(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json(), resp
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None, None

def clean_url(url):
    if not url:
        return None
    parts = list(urlsplit(url))
    parts[3] = ""  # remove query
    return urlunsplit(parts)

def extract_download_links_from_html(html):
    """
    Extract download links for epub, mobi, a4 pdf, and 6-inch pdf.
    Returns dict with keys: 'epub', 'mobi', 'a4_pdf', 'six_inch_pdf'
    """
    links = {"epub": None, "mobi": None, "a4_pdf": None, "six_inch_pdf": None}

    if not html:
        return links

    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href_raw = a["href"]
        href = clean_url(href_raw)
        text = (a.get("title") or a.get_text() or "").lower()

        # EPUB
        if "epub" in href.lower() or "epub" in text:
            if links["epub"] is None:
                links["epub"] = href

        # MOBI
        elif "mobi" in href.lower() or "mobi" in text:
            if links["mobi"] is None:
                links["mobi"] = href

        # A4 PDF
        elif ("a4" in href.lower() and "pdf" in href.lower()) or "a4 pdf" in text:
            if links["a4_pdf"] is None:
                links["a4_pdf"] = href

        # 6-inch PDF
        elif (("6" in href.lower() or "6-inch" in href.lower() or "6 inch" in text) and "pdf" in href.lower()) or "6 inch pdf" in text:
            if links["six_inch_pdf"] is None:
                links["six_inch_pdf"] = href

    return links

def clean_description_from_post(post_obj, max_chars=None):
    yoast = post_obj.get("yoast_head_json", {}) or {}
    desc = yoast.get("description") or yoast.get("og_description") or ""
    if not desc:
        desc = post_obj.get("excerpt", {}).get("rendered") or post_obj.get("content", {}).get("rendered", "")
    text = BeautifulSoup(desc, "html.parser").get_text(separator=" ", strip=True)
    if max_chars and len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "…"
    return text

def slugify(s):
    s = s.lower()
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'[^a-z0-9\-]', '', s)
    return s

# ---------------- CACHES ----------------
AUTHOR_CACHE = {}
CATEGORY_CACHE = {}

def get_author_name(aid):
    if aid in AUTHOR_CACHE:
        return AUTHOR_CACHE[aid]
    data, _ = fetch_json(f"{BASE_URL}/authors/{aid}")
    if isinstance(data, dict):
        name = data.get("name") or data.get("slug") or str(aid)
        AUTHOR_CACHE[aid] = name
        return name
    AUTHOR_CACHE[aid] = str(aid)
    return str(aid)

def get_category_name(cid):
    if cid in CATEGORY_CACHE:
        return CATEGORY_CACHE[cid]
    data, _ = fetch_json(f"{BASE_URL}/genres/{cid}")
    if isinstance(data, dict):
        name = data.get("name") or str(cid)
        CATEGORY_CACHE[cid] = name
        return name
    CATEGORY_CACHE[cid] = str(cid)
    return str(cid)

def fetch_author_names_from_post_object(post_obj):
    names = []
    ids = post_obj.get("authors") or []
    for aid in ids:
        names.append(get_author_name(aid))
    if not names:
        data, _ = fetch_json(f"{BASE_URL}/authors?post={post_obj.get('id')}")
        if isinstance(data, list):
            for d in data:
                names.append(d.get("name") or "")
    return [n for n in names if n]

def fetch_category_names_from_post_object(post_obj):
    names = []
    genre_ids = post_obj.get("genres") or post_obj.get("categories") or []
    for gid in genre_ids:
        names.append(get_category_name(gid))
    if not names:
        data, _ = fetch_json(f"{BASE_URL}/genres?post={post_obj.get('id')}")
        if isinstance(data, list):
            for d in data:
                names.append(d.get("name") or "")
    return [n for n in names if n]

def fetch_contributor_names_from_post_object(post_obj):
    names = []
    data, _ = fetch_json(f"{BASE_URL}/contributors?post={post_obj.get('id')}")
    if isinstance(data, list):
        for d in data:
            names.append(d.get("name") or "")
    return [n for n in names if n]

def fetch_cover_from_post_object(post_obj):
    yy = post_obj.get("yoast_head_json")
    if isinstance(yy, dict):
        og_images = yy.get("og_image") or yy.get("og_images") or []
        if og_images:
            first = og_images[0]
            if isinstance(first, dict):
                url = first.get("url") or first.get("contentUrl")
                if url:
                    return clean_url(url)
    fm = post_obj.get("featured_media")
    if fm:
        data, _ = fetch_json(f"{BASE_URL}/media/{fm}")
        if isinstance(data, dict):
            source = data.get("source_url") or data.get("media_details", {}).get("sizes", {}).get("full", {}).get("source_url")
            if source:
                return clean_url(source)
    data, _ = fetch_json(f"{BASE_URL}/media?parent={post_obj.get('id')}")
    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        src = first.get("source_url")
        if src:
            return clean_url(src)
    return None


def create_opds_entry_from_post(post_obj, seq_number=None, total_estimate=None):
    entry = ET.Element("{%s}entry" % ATOM_NS)

    # dc identifier (UUID)
    uid = str(uuid.uuid4())
    dc_id = ET.SubElement(entry, "{%s}identifier" % DC_NS)
    dc_id.text = f"urn:uuid:{uid}"

    # standard Atom fields
    ET.SubElement(entry, "{%s}id" % ATOM_NS).text = f"urn:ebook:{post_obj.get('id')}"
    ET.SubElement(entry, "{%s}title" % ATOM_NS).text = str(post_obj.get("title") or "")
    ET.SubElement(entry, "{%s}updated" % ATOM_NS).text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # published
    if post_obj.get("date"):
        ET.SubElement(entry, "{%s}published" % ATOM_NS).text = post_obj.get("date")

    # authors
    authors = post_obj.get("authors") or []
    if authors:
        for a in authors:
            a_el = ET.SubElement(entry, "{%s}author" % ATOM_NS)
            ET.SubElement(a_el, "{%s}name" % ATOM_NS).text = a

    # contributors
    contributors = post_obj.get("contributors") or []
    if contributors:
        for c in contributors:
            c_el = ET.SubElement(entry, "{%s}contributor" % ATOM_NS)
            ET.SubElement(c_el, "{%s}name" % ATOM_NS).text = c

    # categories
    cats = post_obj.get("categories") or []
    for cat in cats:
        ET.SubElement(entry, "{%s}category" % ATOM_NS, term=cat, label=cat)
        s = ET.SubElement(entry, "{%s}subject" % DC_NS)
        s.text = cat

    # canonical link
    link_href = post_obj.get("link")
    if link_href:
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="alternate", href=clean_url(link_href))

    # description/summary
    summary_text = post_obj.get("description") or ""
    ET.SubElement(entry, "{%s}summary" % ATOM_NS).text = summary_text

    # Dublin Core language
    dc_lang = ET.SubElement(entry, "{%s}language" % DC_NS)
    dc_lang.text = LANGUAGE

    # publisher
    ET.SubElement(entry, "{%s}publisher" % ATOM_NS).text = PUBLISHER

    # rights
    ET.SubElement(entry, "{%s}rights" % ATOM_NS).text = "Creative Commons"

    # cover image
    cover = post_obj.get("cover")
    if cover:
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="http://opds-spec.org/image", href=cover)
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="http://opds-spec.org/image/thumbnail", href=cover)

    # download links
    downloads = post_obj.get("downloads") or {}
    if downloads.get("epub"):
        ET.SubElement(entry, "{%s}link" % ATOM_NS,
                      rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["epub"]),
                      type="application/epub+zip")
    if downloads.get("mobi"):
        ET.SubElement(entry, "{%s}link" % ATOM_NS,
                      rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["mobi"]),
                      type="application/x-mobipocket-ebook")
    if downloads.get("a4_pdf"):
        ET.SubElement(entry, "{%s}link" % ATOM_NS,
                      rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["a4_pdf"]),
                      type="application/pdf")
    if downloads.get("six_inch_pdf"):
        ET.SubElement(entry, "{%s}link" % ATOM_NS,
                      rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["six_inch_pdf"]),
                      type="application/pdf")

    return entry

''''
# ---------------- OPDS ENTRY ----------------
def create_opds_entry_from_post(post_obj, seq_number=0, total_estimate=0):
    entry = ET.Element("{%s}entry" % ATOM_NS)
    uid = str(uuid.uuid4())
    ET.SubElement(entry, "{%s}identifier" % DC_NS).text = f"urn:uuid:{uid}"
    ET.SubElement(entry, "{%s}id" % ATOM_NS).text = f"urn:ebook:{post_obj.get('id')}"
    ET.SubElement(entry, "{%s}title" % ATOM_NS).text = post_obj.get("title", {}).get("rendered") or ""
    ET.SubElement(entry, "{%s}updated" % ATOM_NS).text = datetime.utcnow().replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if post_obj.get("date"):
        ET.SubElement(entry, "{%s}published" % ATOM_NS).text = post_obj.get("date")

    # Authors
    authors = fetch_author_names_from_post_object(post_obj)
    for a in authors:
        a_el = ET.SubElement(entry, "{%s}author" % ATOM_NS)
        ET.SubElement(a_el, "{%s}name" % ATOM_NS).text = a

    # Contributors
    contributors = fetch_contributor_names_from_post_object(post_obj)
    for c in contributors:
        c_el = ET.SubElement(entry, "{%s}contributor" % ATOM_NS)
        ET.SubElement(c_el, "{%s}name" % ATOM_NS).text = c

    # Categories
    cats = fetch_category_names_from_post_object(post_obj)
    for cat in cats:
        ET.SubElement(entry, "{%s}category" % ATOM_NS, term=cat, label=cat)
        ET.SubElement(entry, "{%s}subject" % DC_NS).text = cat

    # Link canonical
    link_href = post_obj.get("link")
    if link_href:
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="alternate", href=clean_url(link_href))

    # Summary
    ET.SubElement(entry, "{%s}summary" % ATOM_NS).text = clean_description_from_post(post_obj, max_chars=2000)

    # Publisher & language
    ET.SubElement(entry, "{%s}publisher" % ATOM_NS).text = PUBLISHER
    ET.SubElement(entry, "{%s}language" % DC_NS).text = LANGUAGE
    ET.SubElement(entry, "{%s}rights" % ATOM_NS).text = "Free Tamil Ebooks"

    # Cover
    cover = fetch_cover_from_post_object(post_obj)
    if cover:
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="http://opds-spec.org/image", href=cover)
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="http://opds-spec.org/image/thumbnail", href=cover)

    # Downloads
    html_content = post_obj.get("content", {}).get("rendered", "")
    downloads = extract_download_links_from_html(html_content)
    if downloads.get("epub"):
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="http://opds-spec.org/acquisition", href=downloads["epub"], type="application/epub+zip")
    if downloads.get("mobi"):
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="http://opds-spec.org/acquisition", href=downloads["mobi"], type="application/x-mobipocket-ebook")
    if downloads.get("a4_pdf"):
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="http://opds-spec.org/acquisition", href=downloads["a4_pdf"], type="application/pdf")
    if downloads.get("six_inch_pdf"):
        ET.SubElement(entry, "{%s}link" % ATOM_NS, rel="http://opds-spec.org/acquisition", href=downloads["six_inch_pdf"], type="application/pdf")
    return entry
'''

# ---------------- FEEDS ----------------
def create_categories_feed(all_books_data):
    feed = ET.Element("{%s}feed" % ATOM_NS)
    ET.SubElement(feed, "{%s}title" % ATOM_NS).text = "Free Tamil Ebooks - Categories"
    ET.SubElement(feed, "{%s}updated" % ATOM_NS).text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # category -> books
    category_to_books = defaultdict(list)
    for book in all_books_data:
        for cat in book.get("categories", []):
            category_to_books[slugify(cat)].append(book)

    # Entries
    for slug, books in sorted(category_to_books.items()):
        cat_name = books[0]["categories"][0]
        entry = ET.SubElement(feed, "{%s}entry" % ATOM_NS)
        ET.SubElement(entry, "{%s}title" % ATOM_NS).text = cat_name
        ET.SubElement(entry, "{%s}id" % ATOM_NS).text = f"urn:category:{slug}"
        ET.SubElement(entry, "{%s}link" % ATOM_NS,
                      rel="subsection",
                      href=f"{slug}.opds.xml",
                      type="application/atom+xml;profile=opds-catalog;kind=acquisition")
    return feed

def create_category_books_feed(category_slug, books_in_category):
    feed = ET.Element("{%s}feed" % ATOM_NS)
    ET.SubElement(feed, "{%s}title" % ATOM_NS).text = f"Books in category: {category_slug}"
    ET.SubElement(feed, "{%s}updated" % ATOM_NS).text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for book in books_in_category:
        entry = create_opds_entry_from_post(book)
        feed.append(entry)
    return feed

# ---------------- MAIN ----------------
def main():
    all_books_data = []
    book_counter = 0
    stop = False

    for page in range(1, MAX_PAGES + 1):
        if stop:
            break
        url = f"{BASE_URL}/ebooks?per_page={PER_PAGE}&page={page}"
        data, resp = fetch_json(url)
        if not isinstance(data, list) or len(data) == 0:
            break
        for item in data:
            book_counter += 1
            try:
                book_obj = {
                    "id": item.get("id"),
                    "title": item.get("title", {}).get("rendered", ""),
                    "link": item.get("link"),
                    "date": item.get("date"),
                    "yoast_head_json": item.get("yoast_head_json", {}),
                    "excerpt_rendered": item.get("excerpt", {}).get("rendered", ""),
                    "content_rendered": item.get("content", {}).get("rendered", ""),
                }
                book_obj["authors"] = fetch_author_names_from_post_object(item)
                book_obj["contributors"] = fetch_contributor_names_from_post_object(item)
                book_obj["categories"] = fetch_category_names_from_post_object(item)
                book_obj["cover"] = fetch_cover_from_post_object(item)
                book_obj["description"] = clean_description_from_post(item)
                book_obj["downloads"] = extract_download_links_from_html(item.get("content", {}).get("rendered", ""))
                all_books_data.append(book_obj)

                print(f"{book_counter}: {book_obj['title']}")

                if (book_counter % DELAY_INTERVAL) == 0:
                    time.sleep(DELAY_SECONDS)

                if LIMIT_BOOKS and book_counter >= LIMIT_BOOKS:
                    stop = True
                    break
            except Exception as e:
                print(f"Error processing book id {item.get('id')}: {e}", file=sys.stderr)
                continue

    # Save JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_books_data, f, ensure_ascii=False, indent=2)

    # 1️⃣ All books feed
    feed_all = ET.Element("{%s}feed" % ATOM_NS)
    ET.SubElement(feed_all, "{%s}title" % ATOM_NS).text = "Free Tamil Ebooks - All Books"
    ET.SubElement(feed_all, "{%s}updated" % ATOM_NS).text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for book in all_books_data:
        entry = create_opds_entry_from_post(book)
        feed_all.append(entry)
    ET.ElementTree(feed_all).write(OUTPUT_OPDS_ALL, encoding="utf-8", xml_declaration=True)

    # 2️⃣ Categories feed
    feed_cats = create_categories_feed(all_books_data)
    ET.ElementTree(feed_cats).write(OUTPUT_OPDS_CATEGORIES, encoding="utf-8", xml_declaration=True)

    # 3️⃣ Category-specific feeds
    category_to_books = defaultdict(list)
    for book in all_books_data:
        for cat in book.get("categories", []):
            print(f"category = {cat} .")
            print(f"book = {book} . ")
            category_to_books[slugify(cat)].append(book)
    for slug, books in category_to_books.items():
        print(slug)
        if len(slug)<2:
            slug = "no_slug"
        print(slug)
        feed = create_category_books_feed(slug, books)
        ET.ElementTree(feed).write(f"{slug}.opds.xml", encoding="utf-8", xml_declaration=True)

    print(f"Finished. Total books: {book_counter}")

if __name__ == "__main__":
    main()
