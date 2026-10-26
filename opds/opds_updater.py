#!/usr/bin/env python3
"""
opds_updater.py

Helper module to keep FreeTamilEbooks OPDS catalog in sync.
Handles:
- Adding single book to books.json and xml_files/ (called from publish script)
- Syncing any missing books from freetamilebooks.com WordPress REST API
"""
import os
import sys
import re
import json
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET
import html
import requests
from bs4 import BeautifulSoup

# Namespaces
ATOM_NS = "http://www.w3.org/2005/Atom"
DC_NS = "http://purl.org/dc/elements/1.1/"
ET.register_namespace("", ATOM_NS)
ET.register_namespace("dc", DC_NS)

WP_BASE_URL = "https://freetamilebooks.com/wp-json/wp/v2"
PUBLISHER = "FreeTamilEbooks.com by Kaniyam Foundation"
LANGUAGE = "ta"
USER_AGENT = "fte-opds-generator/1.0 (+https://freetamilebooks.com)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}


def slugify(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"[\s\-]+", "_", text)
    text = re.sub(r"[^\w\u0B80-\u0BFF_]", "", text)
    return text


def clean_url(url):
    if not url:
        return None
    parts = list(urlsplit(url))
    parts[3] = ""  # remove query
    return urlunsplit(parts)


def clean_description(desc, max_chars=None):
    if not desc:
        return ""
    text = BeautifulSoup(desc, "html.parser").get_text(separator=" ", strip=True)
    if max_chars and len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + "…"
    return text


def extract_download_links_from_html(html_content):
    links = {"epub": None, "mobi": None, "a4_pdf": None, "six_inch_pdf": None}
    if not html_content:
        return links
    soup = BeautifulSoup(html_content, "html.parser")
    for a in soup.find_all("a", href=True):
        href_raw = a["href"]
        href = clean_url(href_raw)
        text = (a.get("title") or a.get_text() or "").lower()
        if "epub" in href.lower() or "epub" in text:
            if links["epub"] is None:
                links["epub"] = href
        elif "mobi" in href.lower() or "mobi" in text:
            if links["mobi"] is None:
                links["mobi"] = href
        elif ("a4" in href.lower() and "pdf" in href.lower()) or "a4 pdf" in text:
            if links["a4_pdf"] is None:
                links["a4_pdf"] = href
        elif (("6" in href.lower() or "6-inch" in href.lower() or "6 inch" in text) and "pdf" in href.lower()) or "6 inch pdf" in text:
            if links["six_inch_pdf"] is None:
                links["six_inch_pdf"] = href
    return links


AUTHOR_CACHE = {}
CATEGORY_CACHE = {}


def get_author_name(aid):
    if aid in AUTHOR_CACHE:
        return AUTHOR_CACHE[aid]
    try:
        r = requests.get(f"{WP_BASE_URL}/authors/{aid}", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            name = data.get("name") or data.get("slug") or str(aid)
            AUTHOR_CACHE[aid] = name
            return name
    except Exception:
        pass
    AUTHOR_CACHE[aid] = str(aid)
    return str(aid)


def get_category_name(cid):
    if cid in CATEGORY_CACHE:
        return CATEGORY_CACHE[cid]
    try:
        r = requests.get(f"{WP_BASE_URL}/genres/{cid}", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            name = data.get("name") or str(cid)
            CATEGORY_CACHE[cid] = name
            return name
    except Exception:
        pass
    CATEGORY_CACHE[cid] = str(cid)
    return str(cid)


def fetch_author_names(post_obj):
    names = []
    ids = post_obj.get("authors") or []
    for aid in ids:
        names.append(get_author_name(aid))
    return [n for n in names if n]


def fetch_category_names(post_obj):
    names = []
    genre_ids = post_obj.get("genres") or post_obj.get("categories") or []
    for gid in genre_ids:
        names.append(get_category_name(gid))
    return [n for n in names if n]


def fetch_cover_url(post_obj):
    yy = post_obj.get("yoast_head_json")
    if isinstance(yy, dict):
        og_images = yy.get("og_image") or yy.get("og_images") or []
        if og_images and isinstance(og_images[0], dict):
            url = og_images[0].get("url") or og_images[0].get("contentUrl")
            if url:
                return clean_url(url)
    fm = post_obj.get("featured_media")
    if fm:
        try:
            r = requests.get(f"{WP_BASE_URL}/media/{fm}", headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                source = data.get("source_url") or data.get("media_details", {}).get("sizes", {}).get("full", {}).get("source_url")
                if source:
                    return clean_url(source)
        except Exception:
            pass
    return None


def build_book_obj_from_wp(item):
    """Build standardized book dict from WP REST API post object."""
    yoast = item.get("yoast_head_json", {}) or {}
    desc = yoast.get("description") or yoast.get("og_description") or ""
    if not desc:
        desc = item.get("excerpt", {}).get("rendered") or item.get("content", {}).get("rendered", "")

    book_title = item.get("title", {}).get("rendered", "")
    # Unescape HTML entities in title
    book_title = html.unescape(book_title)

    book_obj = {
        "id": item.get("id"),
        "title": book_title,
        "link": item.get("link"),
        "date": item.get("date"),
        "yoast_head_json": yoast,
        "excerpt_rendered": item.get("excerpt", {}).get("rendered", ""),
        "content_rendered": item.get("content", {}).get("rendered", ""),
        "authors": fetch_author_names(item),
        "contributors": [],
        "categories": fetch_category_names(item),
        "cover": fetch_cover_url(item),
        "description": clean_description(desc),
        "downloads": extract_download_links_from_html(item.get("content", {}).get("rendered", ""))
    }
    return book_obj


def create_all_books_entry(book_obj):
    """Create OPDS <entry> for books.opds.xml (includes Dublin Core fields)."""
    entry = ET.Element(f"{{{ATOM_NS}}}entry")
    uid = str(uuid.uuid4())
    ET.SubElement(entry, f"{{{DC_NS}}}identifier").text = f"urn:uuid:{uid}"
    ET.SubElement(entry, f"{{{ATOM_NS}}}id").text = f"urn:ebook:{book_obj.get('id')}"
    ET.SubElement(entry, f"{{{ATOM_NS}}}title").text = str(book_obj.get("title") or "")
    ET.SubElement(entry, f"{{{ATOM_NS}}}updated").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if book_obj.get("date"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}published").text = book_obj.get("date")

    for a in book_obj.get("authors", []):
        a_el = ET.SubElement(entry, f"{{{ATOM_NS}}}author")
        ET.SubElement(a_el, f"{{{ATOM_NS}}}name").text = a

    for c in book_obj.get("contributors", []):
        c_el = ET.SubElement(entry, f"{{{ATOM_NS}}}contributor")
        ET.SubElement(c_el, f"{{{ATOM_NS}}}name").text = c

    for cat in book_obj.get("categories", []):
        ET.SubElement(entry, f"{{{ATOM_NS}}}category", term=cat, label=cat)
        ET.SubElement(entry, f"{{{DC_NS}}}subject").text = cat

    link_href = book_obj.get("link")
    if link_href:
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="alternate", href=clean_url(link_href))

    ET.SubElement(entry, f"{{{ATOM_NS}}}summary").text = book_obj.get("description") or ""
    ET.SubElement(entry, f"{{{DC_NS}}}language").text = LANGUAGE
    ET.SubElement(entry, f"{{{ATOM_NS}}}publisher").text = PUBLISHER
    ET.SubElement(entry, f"{{{ATOM_NS}}}rights").text = "Creative Commons"

    cover = book_obj.get("cover")
    if cover:
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/image", href=cover)
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/image/thumbnail", href=cover)

    downloads = book_obj.get("downloads", {})
    if downloads.get("epub"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["epub"]), type="application/epub+zip")
    if downloads.get("mobi"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["mobi"]), type="application/x-mobipocket-ebook")
    if downloads.get("a4_pdf"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["a4_pdf"]), type="application/pdf")
    if downloads.get("six_inch_pdf"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["six_inch_pdf"]), type="application/pdf")
    return entry


def create_category_entry(book_obj):
    """Create OPDS <entry> for category_<slug>.opds.xml."""
    entry = ET.Element(f"{{{ATOM_NS}}}entry")
    ET.SubElement(entry, f"{{{ATOM_NS}}}title").text = str(book_obj.get("title") or "")
    ET.SubElement(entry, f"{{{ATOM_NS}}}id").text = f"urn:ebook:{book_obj.get('id')}"
    ET.SubElement(entry, f"{{{ATOM_NS}}}updated").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for a in book_obj.get("authors", []):
        a_el = ET.SubElement(entry, f"{{{ATOM_NS}}}author")
        ET.SubElement(a_el, f"{{{ATOM_NS}}}name").text = a

    for cat in book_obj.get("categories", []):
        ET.SubElement(entry, f"{{{ATOM_NS}}}category", term=cat, label=cat)

    if book_obj.get("description"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}summary").text = book_obj["description"]

    cover = book_obj.get("cover")
    if cover:
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/image", href=cover)
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/image/thumbnail", href=cover)

    downloads = book_obj.get("downloads", {})
    if downloads.get("epub"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["epub"]), type="application/epub+zip")
    if downloads.get("mobi"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["mobi"]), type="application/x-mobipocket-ebook")
    if downloads.get("a4_pdf"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["a4_pdf"]), type="application/pdf")
    if downloads.get("six_inch_pdf"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/acquisition",
                      href=clean_url(downloads["six_inch_pdf"]), type="application/pdf")
    return entry


def add_book_to_opds(book_obj, opds_dir="/home/shrini/dev/fte/create_ebooks/opds"):
    """
    Inserts or updates a book in books.json, xml_files/books.opds.xml,
    and category xml files.
    """
    books_json_path = os.path.join(opds_dir, "books.json")
    xml_dir = os.path.join(opds_dir, "xml_files")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Update books.json
    all_books = []
    if os.path.exists(books_json_path):
        with open(books_json_path, "r", encoding="utf-8") as f:
            all_books = json.load(f)

    # Remove existing entry if present, insert at top
    all_books = [b for b in all_books if b.get("id") != book_obj.get("id")]
    all_books.insert(0, book_obj)

    with open(books_json_path, "w", encoding="utf-8") as f:
        json.dump(all_books, f, ensure_ascii=False, indent=2)
    print(f"Updated {books_json_path} (total books: {len(all_books)})")

    # 2. Update xml_files/books.opds.xml
    books_xml_path = os.path.join(xml_dir, "books.opds.xml")
    if os.path.exists(books_xml_path):
        tree = ET.parse(books_xml_path)
        root = tree.getroot()

        # Update root <updated>
        upd = root.find(f"{{{ATOM_NS}}}updated")
        if upd is not None:
            upd.text = now_utc

        # Remove existing entry if present
        book_urn = f"urn:ebook:{book_obj.get('id')}"
        for child in list(root):
            if child.tag == f"{{{ATOM_NS}}}entry":
                id_el = child.find(f"{{{ATOM_NS}}}id")
                if id_el is not None and id_el.text == book_urn:
                    root.remove(child)

        # Insert new entry right after <updated> (index 2)
        new_entry = create_all_books_entry(book_obj)
        root.insert(2, new_entry)

        ET.indent(tree, space="  ")
        tree.write(books_xml_path, encoding="utf-8", xml_declaration=True)
        print(f"Updated {books_xml_path}")

    # 3. Update category feeds and categories.opds.xml
    categories_xml_path = os.path.join(xml_dir, "categories.opds.xml")
    cat_tree = None
    cat_root = None
    if os.path.exists(categories_xml_path):
        cat_tree = ET.parse(categories_xml_path)
        cat_root = cat_tree.getroot()
        upd = cat_root.find(f"{{{ATOM_NS}}}updated")
        if upd is not None:
            upd.text = now_utc

    for cat_name in book_obj.get("categories", []):
        cat_slug = slugify(cat_name)
        if not cat_slug:
            cat_slug = "no_slug"
        cat_file = os.path.join(xml_dir, f"category_{cat_slug}.opds.xml")

        cat_entry = create_category_entry(book_obj)
        book_urn = f"urn:ebook:{book_obj.get('id')}"

        if os.path.exists(cat_file):
            c_tree = ET.parse(cat_file)
            c_root = c_tree.getroot()
            c_upd = c_root.find(f"{{{ATOM_NS}}}updated")
            if c_upd is not None:
                c_upd.text = now_utc
            for child in list(c_root):
                if child.tag == f"{{{ATOM_NS}}}entry":
                    id_el = child.find(f"{{{ATOM_NS}}}id")
                    if id_el is not None and id_el.text == book_urn:
                        c_root.remove(child)
            c_root.insert(2, cat_entry)
            ET.indent(c_tree, space="  ")
            c_tree.write(cat_file, encoding="utf-8", xml_declaration=True)
            print(f"Updated {cat_file}")
        else:
            # Create new category feed
            feed = ET.Element(f"{{{ATOM_NS}}}feed")
            ET.SubElement(feed, f"{{{ATOM_NS}}}title").text = f"Free Tamil Ebooks - {cat_name}"
            ET.SubElement(feed, f"{{{ATOM_NS}}}updated").text = now_utc
            feed.append(cat_entry)
            ET.indent(feed, space="  ")
            ET.ElementTree(feed).write(cat_file, encoding="utf-8", xml_declaration=True)
            print(f"Created new category feed: {cat_file}")

        # Ensure category is listed in categories.opds.xml
        if cat_root is not None:
            cat_urn = f"urn:category:{cat_slug}"
            exists = False
            for child in cat_root.findall(f"{{{ATOM_NS}}}entry"):
                id_el = child.find(f"{{{ATOM_NS}}}id")
                if id_el is not None and id_el.text == cat_urn:
                    exists = True
                    break
            if not exists:
                new_cat_entry = ET.SubElement(cat_root, f"{{{ATOM_NS}}}entry")
                ET.SubElement(new_cat_entry, f"{{{ATOM_NS}}}title").text = cat_name
                ET.SubElement(new_cat_entry, f"{{{ATOM_NS}}}id").text = cat_urn
                ET.SubElement(new_cat_entry, f"{{{ATOM_NS}}}link",
                              rel="subsection",
                              href=f"category_{cat_slug}.opds.xml",
                              type="application/atom+xml;profile=opds-catalog;kind=acquisition")
                print(f"Added '{cat_name}' to {categories_xml_path}")

    if cat_tree is not None:
        ET.indent(cat_tree, space="  ")
        cat_tree.write(categories_xml_path, encoding="utf-8", xml_declaration=True)
        # Keep index.xml in sync with categories.opds.xml
        try:
            import shutil
            shutil.copy2(categories_xml_path, os.path.join(xml_dir, "index.xml"))
        except Exception:
            pass

    # 4. Sync to FTE_opds_catalog git repository for GitHub Pages
    try:
        sync_to_github_pages(opds_dir, f"Add {book_obj.get('title')} ({book_obj.get('id')})")
    except Exception as e:
        print(f"Warning: Failed to sync to GitHub Pages repository: {e}")


def sync_to_github_pages(opds_dir="/home/shrini/dev/fte/create_ebooks/opds", commit_msg="Update OPDS catalog"):
    """
    Syncs generated OPDS feeds, landing page, and books.json to
    /home/shrini/dev/fte/FTE_opds_catalog and pushes to GitHub Pages.
    """
    import subprocess
    import shutil

    fte_catalog_dir = "/home/shrini/dev/fte/FTE_opds_catalog"
    if not os.path.exists(os.path.join(fte_catalog_dir, ".git")):
        return False

    xml_dir = os.path.join(opds_dir, "xml_files")
    if os.path.exists(xml_dir):
        for item in os.listdir(xml_dir):
            s = os.path.join(xml_dir, item)
            d = os.path.join(fte_catalog_dir, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)

    books_json = os.path.join(opds_dir, "books.json")
    if os.path.exists(books_json):
        shutil.copy2(books_json, os.path.join(fte_catalog_dir, "books.json"))

    try:
        # Check if there are changes
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=fte_catalog_dir
        ).decode("utf-8").strip()

        if status:
            print("Deploying OPDS updates to GitHub Pages (KaniyamFoundation/FTE_opds_catalog)...")
            subprocess.check_call(["git", "add", "-A"], cwd=fte_catalog_dir)
            subprocess.check_call(["git", "commit", "-m", commit_msg], cwd=fte_catalog_dir)
            subprocess.check_call(["git", "push", "origin", "main"], cwd=fte_catalog_dir)
            print("✓ Successfully pushed updates to GitHub Pages.")
        else:
            print("GitHub Pages repository is already up to date.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: Git operation in FTE_opds_catalog failed: {e}")
        return False


def sync_missing_books(opds_dir="/home/shrini/dev/fte/create_ebooks/opds"):
    """Finds any books present on freetamilebooks.com but missing in books.json."""
    books_json_path = os.path.join(opds_dir, "books.json")
    existing_ids = set()
    if os.path.exists(books_json_path):
        with open(books_json_path, "r", encoding="utf-8") as f:
            for b in json.load(f):
                existing_ids.add(b.get("id"))

    print(f"Existing books in {books_json_path}: {len(existing_ids)}")
    print("Checking freetamilebooks.com for missing books...")

    page = 1
    missing_items = []
    found_all_existing = False

    while not found_all_existing:
        url = f"{WP_BASE_URL}/ebooks?per_page=20&page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            items = r.json()
            if not items:
                break
            for item in items:
                bid = item.get("id")
                if bid not in existing_ids:
                    missing_items.append(item)
                else:
                    # Since ebooks are in reverse chronological order, once we encounter
                    # books that are already in our catalog, we can stop after checking the page
                    found_all_existing = True
            page += 1
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

    print(f"Found {len(missing_items)} missing books.")

    # Add missing books in chronological order so newest ends up at top
    added_titles = []
    for item in reversed(missing_items):
        book_obj = build_book_obj_from_wp(item)
        print(f"Adding missing book: {book_obj['id']} - {book_obj['title']}")
        add_book_to_opds(book_obj, opds_dir)
        added_titles.append(f"{book_obj['id']}: {book_obj['title']}")

    return added_titles


if __name__ == "__main__":
    opds_path = sys.argv[1] if len(sys.argv) > 1 else "/home/shrini/dev/fte/create_ebooks/opds"
    added = sync_missing_books(opds_path)
    sync_to_github_pages(opds_path, "Manual sync of OPDS catalog")
    print("\nSync completed.")
    if added:
        print("Newly added books:")
        for t in added:
            print(f"  + {t}")
    else:
        print("No missing books found; OPDS catalog is up to date.")
