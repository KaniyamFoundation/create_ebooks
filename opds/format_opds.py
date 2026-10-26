#!/usr/bin/env python3
"""
format_opds.py

1. Fixes category filenames so all Tamil characters (vowels, combining marks, pulli) are preserved.
2. Pretty-prints all OPDS XML files with clean 2-space indentation.
3. Cleans up old malformed category XML files.
4. Updates categories.opds.xml and index.xml with the corrected links.
5. Syncs the changes to FTE_opds_catalog and pushes to GitHub Pages.
"""

import os
import sys
import re
import json
import shutil
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET

ATOM_NS = "http://www.w3.org/2005/Atom"
DC_NS = "http://purl.org/dc/elements/1.1/"
ET.register_namespace("", ATOM_NS)
ET.register_namespace("dc", DC_NS)

OPDS_DIR = "/home/shrini/dev/fte/create_ebooks/opds"
XML_DIR = os.path.join(OPDS_DIR, "xml_files")
FTE_CATALOG_DIR = "/home/shrini/dev/fte/FTE_opds_catalog"


def slugify(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"[\s\-]+", "_", text)
    # Retain Unicode alphanumeric characters, Tamil block (U+0B80-U+0BFF), and underscore
    text = re.sub(r"[^\w\u0B80-\u0BFF_]", "", text)
    return text


def clean_url(url):
    if not url:
        return None
    parts = list(urlsplit(url))
    parts[3] = ""
    return urlunsplit(parts)


def create_category_entry(book_obj):
    entry = ET.Element(f"{{{ATOM_NS}}}entry")
    ET.SubElement(entry, f"{{{ATOM_NS}}}title").text = str(book_obj.get("title") or "")
    ET.SubElement(entry, f"{{{ATOM_NS}}}id").text = f"urn:ebook:{book_obj.get('id')}"

    date_str = book_obj.get("date")
    if date_str:
        if not date_str.endswith("Z"):
            date_str = date_str + "Z"
        ET.SubElement(entry, f"{{{ATOM_NS}}}updated").text = date_str
    else:
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


def run():
    books_json_path = os.path.join(OPDS_DIR, "books.json")
    with open(books_json_path, "r", encoding="utf-8") as f:
        books = json.load(f)

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Pretty-print books.opds.xml
    books_xml_path = os.path.join(XML_DIR, "books.opds.xml")
    if os.path.exists(books_xml_path):
        print(f"Pretty-printing {books_xml_path}...")
        tree = ET.parse(books_xml_path)
        ET.indent(tree, space="  ")
        tree.write(books_xml_path, encoding="utf-8", xml_declaration=True)
        print("  ✓ books.opds.xml formatted.")

    # 2. Group books by category
    category_books = {}
    for b in books:
        for cat in b.get("categories", []):
            cat_name = cat.strip()
            if cat_name:
                category_books.setdefault(cat_name, []).append(b)

    sorted_categories = sorted(category_books.keys())
    print(f"Found {len(sorted_categories)} unique categories across {len(books)} books.")

    # 3. Create clean, pretty category XML files
    valid_category_files = set()
    for cat in sorted_categories:
        slug = slugify(cat)
        cat_filename = f"category_{slug}.opds.xml"
        valid_category_files.add(cat_filename)
        cat_filepath = os.path.join(XML_DIR, cat_filename)

        cat_feed = ET.Element(f"{{{ATOM_NS}}}feed")
        ET.SubElement(cat_feed, f"{{{ATOM_NS}}}title").text = f"Free Tamil Ebooks - {cat}"
        ET.SubElement(cat_feed, f"{{{ATOM_NS}}}updated").text = now_utc

        for b in category_books[cat]:
            cat_feed.append(create_category_entry(b))

        ET.indent(cat_feed, space="  ")
        ET.ElementTree(cat_feed).write(cat_filepath, encoding="utf-8", xml_declaration=True)
        print(f"  ✓ Written: {cat_filename} ({len(category_books[cat])} books)")

    # 4. Generate pretty categories.opds.xml and index.xml
    print("Generating categories.opds.xml & index.xml...")
    cat_index_feed = ET.Element(f"{{{ATOM_NS}}}feed")
    ET.SubElement(cat_index_feed, f"{{{ATOM_NS}}}title").text = "Free Tamil Ebooks - Categories"
    ET.SubElement(cat_index_feed, f"{{{ATOM_NS}}}updated").text = now_utc

    for cat in sorted_categories:
        slug = slugify(cat)
        entry = ET.SubElement(cat_index_feed, f"{{{ATOM_NS}}}entry")
        ET.SubElement(entry, f"{{{ATOM_NS}}}title").text = cat
        ET.SubElement(entry, f"{{{ATOM_NS}}}id").text = f"urn:category:{slug}"
        ET.SubElement(entry, f"{{{ATOM_NS}}}link",
                      rel="subsection",
                      href=f"category_{slug}.opds.xml",
                      type="application/atom+xml;profile=opds-catalog;kind=acquisition")

    ET.indent(cat_index_feed, space="  ")
    categories_xml_path = os.path.join(XML_DIR, "categories.opds.xml")
    index_xml_path = os.path.join(XML_DIR, "index.xml")

    ET.ElementTree(cat_index_feed).write(categories_xml_path, encoding="utf-8", xml_declaration=True)
    ET.ElementTree(cat_index_feed).write(index_xml_path, encoding="utf-8", xml_declaration=True)
    print("  ✓ categories.opds.xml & index.xml generated.")

    # 5. Clean up old malformed category XML files and no_slug.opds.xml
    print("Checking for old malformed XML files to delete...")
    removed_count = 0
    for filename in os.listdir(XML_DIR):
        if filename.startswith("category_") and filename.endswith(".opds.xml"):
            if filename not in valid_category_files:
                os.remove(os.path.join(XML_DIR, filename))
                print(f"  - Removed old corrupted file: {filename}")
                removed_count += 1
        elif filename == "no_slug.opds.xml":
            os.remove(os.path.join(XML_DIR, filename))
            print(f"  - Removed unneeded: {filename}")
            removed_count += 1
    print(f"  Total removed: {removed_count} old files.")

    # 6. Sync to FTE_opds_catalog
    if os.path.exists(os.path.join(FTE_CATALOG_DIR, ".git")):
        print(f"Syncing changes to {FTE_CATALOG_DIR}...")
        # Remove deleted files in FTE_CATALOG_DIR
        for item in os.listdir(FTE_CATALOG_DIR):
            if item.startswith("category_") and item.endswith(".opds.xml"):
                if item not in valid_category_files:
                    os.remove(os.path.join(FTE_CATALOG_DIR, item))
            elif item == "no_slug.opds.xml":
                os.remove(os.path.join(FTE_CATALOG_DIR, item))

        # Copy all updated files from XML_DIR
        for item in os.listdir(XML_DIR):
            s = os.path.join(XML_DIR, item)
            d = os.path.join(FTE_CATALOG_DIR, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)

        # Copy books.json
        shutil.copy2(books_json_path, os.path.join(FTE_CATALOG_DIR, "books.json"))

        # Git status, commit, and push
        subprocess.check_call(["git", "add", "-A"], cwd=FTE_CATALOG_DIR)
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=FTE_CATALOG_DIR
        ).decode("utf-8").strip()

        if status:
            subprocess.check_call(
                ["git", "commit", "-m", "Fix category filenames to preserve Tamil vowels/pulli and pretty-format all XML feeds"],
                cwd=FTE_CATALOG_DIR
            )
            subprocess.check_call(["git", "push", "origin", "main"], cwd=FTE_CATALOG_DIR)
            print("  ✓ Successfully committed and pushed clean OPDS catalog to GitHub Pages.")
        else:
            print("  Repository already clean.")


if __name__ == "__main__":
    run()
