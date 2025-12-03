#!/usr/bin/env python3
"""
generate_category_opds.py

Generate category-based OPDS feeds from existing books.json
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re
import os

# ---------------- CONFIG ----------------
BOOKS_JSON = "books.json"
CATEGORIES_FEED = "categories.opds.xml"
CATEGORY_FEED_PREFIX = "category_"   # will produce category_<slug>.opds.xml
ATOM_NS = "http://www.w3.org/2005/Atom"
DC_NS = "http://purl.org/dc/elements/1.1/"
# ----------------------------------------

ET.register_namespace("", ATOM_NS)
ET.register_namespace("dc", DC_NS)

# slugify helper for category filenames
def slugify(text):
    text = text.lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^\w_]", "", text)
    return text

# Create an OPDS entry for a book object (from books.json)
def create_opds_entry(book):
    entry = ET.Element(f"{{{ATOM_NS}}}entry")
    ET.SubElement(entry, f"{{{ATOM_NS}}}title").text = book.get("title") or ""
    ET.SubElement(entry, f"{{{ATOM_NS}}}id").text = f"urn:ebook:{book.get('id')}"
    ET.SubElement(entry, f"{{{ATOM_NS}}}updated").text = datetime.utcnow().replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # authors
    for author in book.get("authors", []):
        a_el = ET.SubElement(entry, f"{{{ATOM_NS}}}author")
        ET.SubElement(a_el, f"{{{ATOM_NS}}}name").text = author

    # categories
    for cat in book.get("categories", []):
        ET.SubElement(entry, f"{{{ATOM_NS}}}category", term=cat, label=cat)

    # description
    if book.get("description"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}summary").text = book["description"]

    # cover
    if book.get("cover"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/image", href=book["cover"])
        ET.SubElement(entry, f"{{{ATOM_NS}}}link", rel="http://opds-spec.org/image/thumbnail", href=book["cover"])

    # download links
    downloads = book.get("downloads", {})
    if downloads.get("epub"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link",
                      rel="http://opds-spec.org/acquisition",
                      href=downloads["epub"],
                      type="application/epub+zip")
    if downloads.get("mobi"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link",
                      rel="http://opds-spec.org/acquisition",
                      href=downloads["mobi"],
                      type="application/x-mobipocket-ebook")
    if downloads.get("a4_pdf"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link",
                      rel="http://opds-spec.org/acquisition",
                      href=downloads["a4_pdf"],
                      type="application/pdf")
    if downloads.get("six_inch_pdf"):
        ET.SubElement(entry, f"{{{ATOM_NS}}}link",
                      rel="http://opds-spec.org/acquisition",
                      href=downloads["six_inch_pdf"],
                      type="application/pdf")

    return entry

# Create a category OPDS feed from a list of books
def create_category_feed(category_name, books_in_category):
    feed = ET.Element(f"{{{ATOM_NS}}}feed")
    ET.SubElement(feed, f"{{{ATOM_NS}}}title").text = f"Free Tamil Ebooks - {category_name}"
    ET.SubElement(feed, f"{{{ATOM_NS}}}updated").text = datetime.utcnow().replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for book in books_in_category:
        entry = create_opds_entry(book)
        feed.append(entry)

    return feed

# Save XML tree
def save_feed(tree, path):
    ET.ElementTree(tree).write(path, encoding="utf-8", xml_declaration=True)
    print(f"Saved {path}")

def main():
    # Load all books
    with open(BOOKS_JSON, "r", encoding="utf-8") as f:
        all_books = json.load(f)

    # Build unique category map
    category_map = {}  # slug -> display name
    for book in all_books:
        for cat in book.get("categories", []):
            slug = slugify(cat)
            category_map[slug] = cat

    # Create categories.opds.xml
    feed_all = ET.Element(f"{{{ATOM_NS}}}feed")
    ET.SubElement(feed_all, f"{{{ATOM_NS}}}title").text = "Free Tamil Ebooks - Categories"
    ET.SubElement(feed_all, f"{{{ATOM_NS}}}updated").text = datetime.utcnow().replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for slug, display_name in category_map.items():
        entry = ET.SubElement(feed_all, f"{{{ATOM_NS}}}entry")
        ET.SubElement(entry, f"{{{ATOM_NS}}}title").text = display_name
        ET.SubElement(entry, f"{{{ATOM_NS}}}id").text = f"urn:category:{slug}"
        ET.SubElement(entry, f"{{{ATOM_NS}}}link",
                      rel="subsection",
                      href=f"{CATEGORY_FEED_PREFIX}{slug}.opds.xml",
                      type="application/atom+xml;profile=opds-catalog;kind=acquisition")

        # create category feed
        books_in_cat = [b for b in all_books if display_name in b.get("categories", [])]
        cat_feed = create_category_feed(display_name, books_in_cat)
        save_feed(cat_feed, f"{CATEGORY_FEED_PREFIX}{slug}.opds.xml")

    save_feed(feed_all, CATEGORIES_FEED)
    print(f"Generated category feeds. Total categories: {len(category_map)}")

if __name__ == "__main__":
    main()
