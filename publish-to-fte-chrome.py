# -*- coding: utf-8 -*-
from urllib.request import urlopen

import urllib
import shutil

import unittest, time, re
import os
import re
import yaml
import sys
import time
import uuid
import shutil
import json
import argparse
import requests
import base64
from datetime import datetime, timezone


from github import Github

from mastodon import Mastodon
#from mailjet_rest import Client
import mailjet_rest

#https://www.zenrows.com/blog/selenium-cloudflare-bypass#cloudflare-bypass-using-zenrows
#import undetected_chromedriver as uc 



parser = argparse.ArgumentParser()

parser.add_argument('-l','--local-file', help='Use Local File', required=False)
parser.add_argument('-r','--remote-book-url', help='Use Remote File', required=False)
parser.add_argument('-i','--interactive', help='Interactive Mode', required=False)
parser.add_argument('-bn','--book_number', help='Book Number', required=True)
parser.add_argument('-issue','--github_issue_number',help = "Github Issue number", required=False)

parser.add_argument('-epub','--epub-id',help = "epub id", required=False)
parser.add_argument('-a4_pdf','--a4-pdf-id',help = "A4 PDF id", required=False)
parser.add_argument('-sixinch_pdf','--six-inch-pdf-id',help = "6 inch PDF id", required=False)
parser.add_argument('--skip-ia-check', action='store_true', help='Skip Internet Archive verification', required=False)                                                                                                                  


args = parser.parse_args()

local_file = args.local_file
remote_book_url = args.remote_book_url
interactive = args.interactive
book_number = args.book_number
github_issue_number = int(args.github_issue_number)

epub_id = args.epub_id
a4_id = args.a4_pdf_id
sixinch_id = args.six_inch_pdf_id


home = os.getenv("HOME")

fte_yaml = yaml.full_load(open(home + '/.config/fte-login.yaml'))

fte_username = fte_yaml['username']
fte_password = fte_yaml['password']

git_username = fte_yaml['git_username']
git_password = fte_yaml['git_password']


android_push_Authorization = fte_yaml['android_push_Authorization']


mastodon_access_token = fte_yaml['mastodon_access_token']
mastodon_url = fte_yaml['mastodon_url']


mailjet_api_key = fte_yaml['mailjet_api_key']
mailjet_api_secret = fte_yaml['mailjet_api_secret']


telegram_token = fte_yaml['telegram_token']
telegram_channel_chat_id = fte_yaml['telegram_channel_chat_id']




fte_app_password = fte_yaml.get('wp_app_password') or fte_yaml.get('app_password') or fte_password
wp_auth = (fte_username, fte_app_password)
wp_api_base = "https://freetamilebooks.com/wp-json/wp/v2"

# Download Monitor REST API configuration
dlm_public_key = fte_yaml.get('dlm_public_key', '5dd447cee8e467d1caffbe619f8bffaa')
dlm_secret_key = fte_yaml.get('dlm_secret_key', 'e464da51f8667be06a231669d8d2d1cf')
dlm_headers = {
    'X-DLM-API-Key': dlm_public_key,
    'X-DLM-API-Secret': dlm_secret_key
}
dlm_api_base = "https://freetamilebooks.com/wp-json/download-monitor/v1"

# Verify WordPress REST API credentials upfront
auth_check = requests.get(f"{wp_api_base}/users/me", auth=wp_auth)
if auth_check.status_code == 401:
    print("\n" + "=" * 60)
    print("ERROR: WordPress REST API Authentication failed (401 Unauthorized).")
    print("Regular WordPress passwords cannot be used with the REST API.")
    print("Please generate an Application Password:")
    print("  1. Log in to https://freetamilebooks.com/wp-admin/profile.php")
    print("  2. Scroll down to 'Application Passwords'")
    print("  3. Enter a name (e.g. 'fte-script') and click 'Add New Application Password'")
    print("  4. Add the generated password to ~/.config/fte-login.yaml:")
    print("       wp_app_password: \"xxxx xxxx xxxx xxxx xxxx xxxx\"")
    print("=" * 60 + "\n")
    sys.exit(1)


#print("Try after one hour")
#sys.exit()



def send_image_to_telegram(image):

    img = open(image,'rb')        
    api_url = f'https://api.telegram.org/bot{telegram_token}/sendPhoto?chat_id={telegram_channel_chat_id}'
    try:
        response = (requests.post(api_url, files={'photo': img}))
        print(response.text)
    except Exception as e:
        print(e)


    '''    
    print(image)
    print(telegram_token)
    print(telegram_channel_chat_id)
    apiURL = f'https://api.telegram.org/bot{telegram_token}/sendPhoto'
    print(apiURL)
    try:
        response = requests.post(apiURL, json={'chat_id': telegram_channel_chat_id, 'photo': image})
        print(response.text)
    except Exception as e:
        print(e)
    '''


def send_text_to_telegram(message):
    apiURL = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    try:
        response = requests.post(apiURL, json={'chat_id': telegram_channel_chat_id, 'text': message})
        print(response.text)
    except Exception as e:
        print(e)



if remote_book_url:
    book_url = remote_book_url


    print("Getting Book Info")
    book_info = yaml.full_load(urlopen(book_url.replace('details','download') + '/book-info.yaml'))


    book_title = book_info['book_title']
    print(book_title)

    book_title_in_english = book_info['book_title_in_english'].replace(" ","_").replace("-","_")
    author = book_info['author']
    print(author)
    category  = book_info['category']
    print(category)
    if book_info['author_mail']:
        author_mail = book_info['author_mail']
    else:
        author_mail = ""

    cover_image = book_info['cover_image']


    if book_info['artist']:
        artist = book_info['artist']
    else:
        artist = ""

    if book_info['artist_email']:
        artist_email = book_info['artist_email']
    else:
        artist_email = ""

    if book_info['translator']:
        translator = book_info['translator']
    else:
        translator = ""

    if book_info['translator_email']:
        translator_email = book_info['translator_email']
    else:
        translator_email = ""

    if 'author_communication' in book_info:
        if book_info['author_communication']:
            author_communication = book_info['author_communication']
        else:
            author_communication = "" 
    else:
        author_communication = "" 

            
    if 'author_communication_email' in book_info:
        if book_info['author_communication_email']:
            author_communication_email = book_info['author_communication_email']
        else:
            author_communication_email = "" 
    else:
        author_communication_email = "" 

            
    if 'ocr_proofread' in book_info:
        if book_info['ocr_proofread']:
            ocr_proofread = book_info['ocr_proofread']
        else:
            ocr_proofread = "" 
    else:
        ocr_proofread = "" 

    if 'ocr_proofread_email' in book_info:
        if book_info['ocr_proofread_email']:
            ocr_proofread_email = book_info['ocr_proofread_email']
        else:
            ocr_proofread_email = "" 
    else:
        ocr_proofread_email = "" 
            

    ebook_maker = book_info['ebook_maker']
    ebook_maker_email = book_info['ebook_maker_email']
    license = book_info['license']




    epub_url = book_url.replace('details','download') + "/" +  book_title_in_english + ".epub"
    a4_pdf_url  = book_url.replace('details','download') + "/" +  book_title_in_english + "_a4.pdf"
    six_inch_pdf_url = book_url.replace('details','download') + "/" +  book_title_in_english + "_6_inch.pdf"
    cover_url = book_url.replace('details','download') + "/" +  cover_image


if interactive == "yes":

    book_title = input("Book Title : ").strip()
    book_title_in_english = input("Book Title in English : ").strip()
    book_url = input("Book Archive URL : ").strip()
    author = input("Author : ").strip()
    author_mail = input("Author Mail : ").strip()
    artist = input("Artist : ").strip()
    artist_email = input("Artist Email : ").strip()
    translator = input("Translator : ").strip()
    translator_email = input("Translator Email : ").strip()
    ebook_maker = input("Ebook made by : ").strip()
    ebook_maker_email = input("Ebook Maker email : ").strip()
    license = input("License : ").strip()
    category = input("category : ").strip()

    cover_url = input("Cover Image URL : ").strip()
    epub_url = input("Epub URL : ").strip()
    a4_pdf_url  = input("A4 PDF URL : ").strip()
    six_inch_pdf_url = input("Six inch PDF URL : ")
    
    cover_image = book_title_in_english + "_cover.jpg"



def get_ia_identifier(url_or_id):
    cleaned = url_or_id.strip().rstrip('/')
    match = re.search(r'archive\.org/(?:details|download)/([^/?#]+)', cleaned)
    if match:
        return match.group(1)
    return cleaned.split('/')[-1]


def check_ia_tasks(identifier):
    """Returns (summary_dict, tasks_list) for the given IA identifier."""
    try:
        import internetarchive as ia
        item = ia.get_item(identifier)
        summary = item.get_task_summary()
        tasks = item.tasks or []
        return summary, tasks
    except Exception:
        url = f"https://archive.org/metadata/{identifier}/tasks"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                res = r.json().get("result", [])
                summary = {
                    "queued": sum(1 for t in res if t.get("status") == "queued"),
                    "running": sum(1 for t in res if t.get("status") == "running"),
                    "error": sum(1 for t in res if t.get("status") == "error"),
                    "paused": sum(1 for t in res if t.get("status") == "paused"),
                }
                return summary, res
            elif r.status_code == 404 or "error" in r.text:
                return {"queued": 0, "running": 0, "error": 0, "paused": 0}, []
        except Exception:
            pass
        return {"queued": 0, "running": 0, "error": 0, "paused": 0}, []


def verify_file_url(url, timeout=15):
    """Check if remote file is accessible and returns 200 (following 302 redirects)."""
    try:
        r = requests.get(url, stream=True, allow_redirects=True, timeout=timeout)
        if r.status_code == 200:
            return True, r.status_code, ""
        return False, r.status_code, f"HTTP {r.status_code}"
    except Exception as e:
        return False, 0, str(e)


def wait_for_ia_ready(book_url, file_urls, poll_interval=20, max_wait_minutes=30):
    identifier = get_ia_identifier(book_url)
    print("\n" + "=" * 60)
    print(f"Checking Internet Archive status for: {identifier}")
    print("=" * 60)

    start_time = time.time()
    while True:
        summary, tasks = check_ia_tasks(identifier)

        # Ingestion tasks that must finish before files are stable
        ingestion_tasks = [
            t for t in (tasks or [])
            if t.get("cmd") in ["archive.php", "book_op.php", "bup.php"]
            and t.get("status") in ["queued", "running", "waiting"]
        ]

        # Verify all files respond with HTTP 200
        pending_files = []
        for u in file_urls:
            ok, status, err = verify_file_url(u)
            fname = u.split('/')[-1]
            if not ok:
                pending_files.append((fname, status, err))

        if len(ingestion_tasks) == 0 and len(pending_files) == 0:
            print("✓ All files accessible and verified on Internet Archive:")
            for u in file_urls:
                print(f"  - {u.split('/')[-1]}: OK (HTTP 200)")

            other_tasks = [
                f"{t.get('cmd')} ({t.get('status')})" for t in (tasks or [])
            ]
            if other_tasks:
                print(f"  (Note: IA background tasks queued/running: {', '.join(other_tasks)})")
            print("Proceeding to publish the book.\n")
            break

        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)

        reasons = []
        if ingestion_tasks:
            t_names = ', '.join(f"{t.get('cmd')} ({t.get('status')})" for t in ingestion_tasks)
            reasons.append(f"Ingestion tasks in progress: {t_names}")
        if pending_files:
            f_names = ', '.join(f"{fn} ({st})" for fn, st, _ in pending_files)
            reasons.append(f"Files not accessible yet: {f_names}")

        print(f"[{mins:02d}:{secs:02d}] IA processing: {'; '.join(reasons)}. Waiting {poll_interval}s...")

        if elapsed > max_wait_minutes * 60:
            print(f"\nWarning: Waited {max_wait_minutes} minutes, but files are still not ready.")
            if sys.stdin.isatty():
                choice = input("Do you want to continue publishing anyway? (y/n): ").strip().lower()
                if choice == 'y':
                    break
            print("Aborting publish. Please try again once IA finishes processing.")
            sys.exit(1)

        time.sleep(poll_interval)


def get_download_url(download_id):
    r = requests.get(f"{wp_api_base}/dlm_download/{download_id}", auth=wp_auth)
    if r.status_code == 200:
        return r.json().get("link")
    return f"https://freetamilebooks.com/download/{download_id}/"


def add_download(filename, file_url):
    print("Adding Download via REST API:", filename)
    # 1. Create the download post (explicitly set _members_only=False so downloads are public)
    r_dl = requests.post(
        f"{dlm_api_base}/download",
        headers=dlm_headers,
        json={
            "title": filename,
            "_members_only": False,
            "_redirect_only": "yes",
            "_featured": "no",
            "_new_tab": "yes"
        }
    )
    if r_dl.status_code not in [200, 201]:
        raise Exception(f"Failed to create download '{filename}': {r_dl.status_code} - {r_dl.text}")
    dl_id = r_dl.json().get("download_id")

    # 2. Attach the Archive.org file URL (version)
    r_ver = requests.post(
        f"{dlm_api_base}/version",
        headers=dlm_headers,
        json={
            "download_id": dl_id,
            "version": "1.0",
            "url": file_url
        }
    )
    if r_ver.status_code not in [200, 201]:
        print(f"Warning: Failed to attach version for '{filename}': {r_ver.status_code} - {r_ver.text}")

    # 3. Explicitly ensure _members_only is False and _redirect_only is 'yes'
    requests.patch(
        f"{dlm_api_base}/download/{dl_id}",
        headers=dlm_headers,
        json={
            "_members_only": False,
            "_redirect_only": "yes"
        }
    )

    # 4. Get the public download link
    dl_url = get_download_url(dl_id)

    print(f"  -> Added {filename} (ID: {dl_id}, Link: {dl_url})")
    return (dl_id, dl_url)


if not args.skip_ia_check:
    wait_for_ia_ready(book_url, [epub_url, a4_pdf_url, six_inch_pdf_url, cover_url])

print("Adding Downloads via Download Monitor REST API...")

if epub_id:
    epub_data = [epub_id, get_download_url(epub_id)]
else:
    epub_data = add_download(book_title + " epub", epub_url)

if a4_id:
    a4_pdf_data = [a4_id, get_download_url(a4_id)]
else:
    a4_pdf_data = add_download(book_title + " A4 PDF", a4_pdf_url)

if sixinch_id:
    six_inch_pdf_data = [sixinch_id, get_download_url(sixinch_id)]
else:
    six_inch_pdf_data = add_download(book_title + " 6 inch PDF", six_inch_pdf_url)


with urllib.request.urlopen(cover_url) as response, open(cover_image, 'wb') as out_file:
    shutil.copyfileobj(response, out_file)
print("Downloaded Cover Image")

filename = cover_image

# Optimize cover image for web & WhatsApp (WhatsApp drops preview if image > 300 KB or incompatible format)
try:
    from PIL import Image
    with Image.open(filename) as im:
        rgb_im = im.convert("RGB")
        opt_filename = os.path.splitext(filename)[0] + "_web.jpg"
        rgb_im.save(opt_filename, "JPEG", quality=85, optimize=True)
        if os.path.getsize(opt_filename) > 300 * 1024:
            rgb_im.save(opt_filename, "JPEG", quality=75, optimize=True)
        filename = opt_filename
        print(f"Optimized cover image for web/WhatsApp preview: {os.path.getsize(filename)} bytes")
except Exception as e:
    print(f"Warning: Could not optimize image ({e}), uploading original.")

print("Uploading cover Image to WordPress...")
with open(filename, 'rb') as img_f:
    img_bytes = img_f.read()

content_type = 'image/png' if filename.lower().endswith('.png') else 'image/jpeg'
media_headers = {
    'Content-Disposition': f'attachment; filename="{os.path.basename(filename)}"',
    'Content-Type': content_type,
}

media_resp = requests.post(f"{wp_api_base}/media", auth=wp_auth, headers=media_headers, data=img_bytes)
if media_resp.status_code not in [200, 201]:
    raise Exception(f"Failed to upload cover image: {media_resp.status_code} {media_resp.text}")

media_data = media_resp.json()
image_url = media_data.get("source_url") or media_data.get("guid", {}).get("rendered", "")
attachment_id = media_data["id"]
print("Uploaded cover Image:", image_url)


content = '''<!-- wp:post-featured-image {"aspectRatio":"2/3","align":"center"} /-->

<!-- wp:paragraph -->
<p><b>Download ebooks</b></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Android, iOS, Kindle கருவிகளில் படிக்க</p>
<!-- /wp:paragraph -->

<!-- wp:shortcode -->'''

content = content + '[download id="' + str(epub_data[0]) + '" template="button"]'

content = content + '''
<!-- /wp:shortcode -->

<!-- wp:paragraph -->
<p>கணினிகளில் படிக்க, அச்சடிக்க</p>
<!-- /wp:paragraph -->

<!-- wp:shortcode -->'''


content = content + '[download id="' + str(a4_pdf_data[0]) +  '" template="button"]'

content = content + '''
<!-- /wp:shortcode -->

<!-- wp:paragraph -->
<p>செல்பேசிகளில் படிக்க</p>
<!-- /wp:paragraph -->

<!-- wp:shortcode -->'''


content = content + '[download id="' + str(six_inch_pdf_data[0]) + '" template="button"]'

content= content + '''
<!-- /wp:shortcode -->

<!-- wp:paragraph -->'''

content = content + '<p>நூல் : ' + book_title + '</p>'


content = content +'''
<!-- /wp:paragraph -->

<!-- wp:paragraph -->'''


content = content + '<p>ஆசிரியர் : ' + author + '</p>'

content = content +'''
<!-- /wp:paragraph -->

<!-- wp:details -->'''

content = content + '<details class="wp-block-details"><summary>புத்தகம் குறித்த கூடுதல் தகவல்</summary><!-- wp:paragraph -->'

content = content + '<p>அட்டைப்படம் : ' +  artist + '</p>'
content = content +'''
<!-- /wp:paragraph -->

<!-- wp:paragraph -->'''


content = content + '<p>மின்னூலாக்கம் : ' + ebook_maker + '</p>'
content = content +'''

<!-- /wp:paragraph -->

<!-- wp:paragraph -->

<p>வெளியீடு : FreeTamilEbooks.com</p>


<!-- /wp:paragraph -->

<!-- wp:paragraph -->'''

content = content + '<p>உரிமை : ' + license + '</p>'
content = content +'''

<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>உரிமை – கிரியேட்டிவ் காமன்ஸ். எல்லாரும் படிக்கலாம், பகிரலாம்.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->'''

content = content + '<p>பிற வடிவங்களில் படிக்க – <a href="' + book_url + '">Archive.org</a></p>'
content = content +'''

<!-- /wp:paragraph -->

<!-- wp:paragraph -->'''

content = content + '<p>புத்தக எண் - ' + str(book_number) + '</p>'

content = content +'''

<!-- /wp:paragraph --></details>
<!-- /wp:details -->
'''


print("Publising the Ebook")  
#content = content + extra

'''
postDict = {
    "title": book_title + " - " + category + " - " + author ,
    "content": content, 
    "slug":  book_title_in_english,
    "status": "publish", 

    "categories": categoryIdList, # [1374]
    "tags": tagIdList, # [1367, 13224, 13225, 13226]
    # TODO: featured_media, excerpt
}
'''

def get_or_create_term(taxonomy, term_name, auth):
    term_name = term_name.strip()
    if not term_name:
        return None
    tax_url = f"{wp_api_base}/{taxonomy}"
    # Search existing term
    search_resp = requests.get(tax_url, params={"search": term_name}, auth=auth)
    if search_resp.status_code == 200:
        for t in search_resp.json():
            if t.get("name", "").strip().lower() == term_name.lower():
                return t["id"]
    # If not found, create new term
    create_resp = requests.post(tax_url, json={"name": term_name}, auth=auth)
    if create_resp.status_code == 201:
        return create_resp.json()["id"]
    elif create_resp.status_code == 400 and create_resp.json().get("code") == "term_exists":
        return create_resp.json().get("data", {}).get("resource_id")
    # Fallback to first search result if any
    if search_resp.status_code == 200 and len(search_resp.json()) > 0:
        return search_resp.json()[0]["id"]
    print(f"Warning: could not resolve {taxonomy} for '{term_name}'")
    return None

genre_ids = []
if category:
    gid = get_or_create_term("genres", category, wp_auth)
    if gid:
        genre_ids.append(gid)

author_ids = []
if author:
    aid = get_or_create_term("authors", author, wp_auth)
    if aid:
        author_ids.append(aid)

post_payload = {
    "title": book_title,
    "slug": book_title_in_english,
    "content": content,
    "status": "publish",
    "comment_status": "open",
    "featured_media": attachment_id,
}
if genre_ids:
    post_payload["genres"] = genre_ids
if author_ids:
    post_payload["authors"] = author_ids

print("Publishing ebook post via REST API...")
post_resp = requests.post(f"{wp_api_base}/ebooks", auth=wp_auth, json=post_payload)
if post_resp.status_code not in [200, 201]:
    raise Exception(f"Failed to publish post: {post_resp.status_code} - {post_resp.text}")

print("Published")

# ----------------- Update OPDS Catalog -----------------
print("Updating OPDS catalog...")
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    opds_dir = None
    for cand in [
        os.path.join(script_dir, "opds"),
        os.path.join(os.path.dirname(script_dir), "opds"),
        "/home/shrini/dev/fte/create_ebooks/opds"
    ]:
        if os.path.exists(os.path.join(cand, "books.json")):
            opds_dir = cand
            break

    if opds_dir:
        if opds_dir not in sys.path:
            sys.path.insert(0, opds_dir)
        import opds_updater

        post_data = post_resp.json()
        post_id = post_data.get("id")
        post_link = post_data.get("link") or f"https://freetamilebooks.com/ebooks/{book_title_in_english}/"
        post_date = post_data.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        downloads = {
            "epub": epub_data[1] if epub_data else None,
            "mobi": None,
            "a4_pdf": a4_pdf_data[1] if a4_pdf_data else None,
            "six_inch_pdf": six_inch_pdf_data[1] if six_inch_pdf_data else None,
        }

        summary_text = f"Download ebooks Android, iOS, Kindle கருவிகளில் படிக்க கணினிகளில் படிக்க, அச்சடிக்க செல்பேசிகளில் படிக்க நூல் : {book_title} ஆசிரியர் : {author}"

        book_obj = {
            "id": post_id,
            "title": book_title,
            "link": post_link,
            "date": post_date,
            "authors": [author] if author else [],
            "contributors": [c for c in [artist, ebook_maker] if c],
            "categories": [category] if category else [],
            "cover": image_url,
            "description": summary_text,
            "downloads": downloads
        }

        opds_updater.add_book_to_opds(book_obj, opds_dir)
        print("✓ OPDS catalog successfully updated with new book.")
    else:
        print("Warning: opds directory not found. Skipping OPDS catalog update.")
except Exception as e:
    print(f"Warning: Failed to update OPDS catalog: {e}")


if os.path.exists(cover_image):
    os.remove(cover_image)
if os.path.exists(filename):
    os.remove(filename)


book_name = book_title
bookid = str(uuid.uuid4())
cover_image = image_url
gen = category
epub_link = epub_data[1]
authors = author
url =   "https://freetamilebooks.com/ebooks/" + book_title_in_english



data = {}
data["title"] = book_name
data["bookid"] = bookid
data["author"] = author
data["image"] = cover_image
data["epub"] = epub_link
data["category"] = category

'''
xml_content = "\n\n" + "<book>" +"\n" + "<bookid>" + bookid + "</bookid>" + "\n" + "<title>" + book_name + "</title>" + "\n"
xml_content = xml_content + "<author>" + authors + "</author>" + "\n"
xml_content = xml_content + "<image>" + cover_image + "</image>" + "\n"
xml_content = xml_content + "<link>" + url + "</link>" + "\n"
xml_content = xml_content + "<epub>" + epub_link + "</epub>" + "\n"
xml_content = xml_content + "<pdf />" + "\n"
xml_content = xml_content + "<category>" + gen + "</category>" + "\n"
xml_content = xml_content + "<date />" + "\n" + "</book>" + "\n"

#print(xml_content)
'''
print("Adding into booksdb.json\n")



git_clone = "git clone https://" + git_username +":" + git_password + "@github.com/KaniyamFoundation/Free-Tamil-Ebooks fte_repo >  git.log 2>&1"
os.system(git_clone)

'''
temp = open('temp', 'w')
with open('fte_repo/booksdb.json','r') as f:
    for line in f:
        if line.startswith('<books>'):
            line = line + xml_content
        temp.write(line)
temp.close()
shutil.move('temp', 'fte_repo/booksdb.xml')
'''


with open('fte_repo/booksdb.json') as f:
    existing_data = json.load(f)

existing_data['books'].insert(0,data)


with open('fte_repo/booksdb.json', 'w') as f:
    json.dump(existing_data,f,indent=2, sort_keys=False,ensure_ascii=False)


os.chdir('fte_repo')
git_add = "git add booksdb.json >>  git.log 2>&1"
os.system(git_add)


git_commit = "git commit -m 'added a book' >>  git.log 2>&1"
os.system(git_commit)

git_push = "git push origin master >>  git.log 2>&1"
os.system(git_push)

os.chdir('../')
os.system("rm -rf fte_repo")

print("Done")

print("Sending Push Notification to Android Devices")

title = "புது மின்னூல் - " + book_title
text = "FreeTamilEbooks ன் புதிய மின்னூல் வெளியிடப்பட்டுள்ளது. " + book_title  + " " + author + ".  இன்றே படியுங்கள். "



headers = {'Authorization': android_push_Authorization}
headers = json.dumps(headers,ensure_ascii=False)
header_json = json.loads(headers)


data = {'notification':{'title': title, 'text': text }, 'data' : { 'keyname': 'shrini' },'to' : '/topics/fte_books'}
data = json.dumps(data,ensure_ascii=False)
data_json = json.loads(data)



api = "https://fcm.googleapis.com/fcm/send"

r = requests.post(api, json=data_json, headers=header_json)

#print(r.json())


mailjet = mailjet_rest.Client(auth=(mailjet_api_key, mailjet_api_secret), version='v3.1')



if len(artist_email.strip()) <2:
    artist_email = "kaniyamfoundation@gmail.com"

if len(artist.strip()) <2:
    artist = "Kaniyam Foundation"


if len(translator_email.strip()) <2:
    translator_email = "kaniyamfoundation@gmail.com"

if len(translator.strip()) <2:
    translator = "Kaniyam Foundation"


if len(ebook_maker_email.strip()) <2:
    ebook_maker_email = "kaniyamfoundation@gmail.com"


if len(ebook_maker.strip()) <2:
    ebook_maker = "Kaniyam Foundation"


    

if len(author_mail.strip()) < 2:
    author_mail = "kaniyamfoundation@gmail.com"



text =  "வணக்கம் " + author + ", \n" \
            'உங்கள் மின்னூல் ' + book_name + ' வெளியிடப்பட்டது. \n' \
            'இங்கே பார்க்கவும். ' + url +"\n\n" \
            'உங்கள் தொடர்ந்த ஆதரவுக்கு மிக்க நன்றி! \n\n' \
            'அன்புடன்,\n' \
            'FreeTamilEbooks.com தன்னார்வலர்கள்'

data = {
      'Messages': [
				{
						"From": {
								"Email": "publisher@freetamilebooks.com",
								"Name": "Publisher FreeTamilEbooks.com"
						},
						"To": [
								{
										"Email": author_mail,
										"Name": author
								}
						],
						"CC": [
								{
										"Email": "kaniyamfoundation@gmail.com",
										"Name": "கணியம் அறக்கட்டளை"
								},

                                {
                                        "Email": artist_email,
                                        "Name": artist
                                },
                                {
                                        "Email": translator_email,
                                        "Name": translator
                                },
                                {
                                        "Email": ebook_maker_email,
                                        "Name": ebook_maker
                                }                                
                                
						],


						"Subject": 'உங்கள் மின்னூல் ' + book_name + ' வெளியிடப்பட்டது.',
						"TextPart": text,
				}
		]
        }
result = mailjet.send.create(data=data)
print(result.status_code)
print(result.json())


mastodon = Mastodon(
    access_token = mastodon_access_token,
    api_base_url = mastodon_url
)


toot = "மின்னூல்: " + book_name + "\n" \
        " " + url + "\n" \
        "உரிமை: கிரியேட்டிவ் காமன்சு.படிக்கலாம்,பகிரலாம். \n" \
        " #Tamil #Ebooks #Kaniyam #தமிழ் #கணியம் #CreativeCommons"

mastodon.status_post(toot)



print("Done")

os.system("rm *.log")

print("Book URL is : " + url)



if github_issue_number:

    g = Github(git_username, git_password)

    repo = g.get_repo("KaniyamFoundation/Ebooks")
    issue = repo.get_issue(number=github_issue_number)


    body = "இங்கே வெளியிட்டுள்ளோம் - " + url
    issue.create_comment(body)


    issue.edit(state="closed")
    
    issue.delete_labels()  
    print("Closed the issue https://github.com/KaniyamFoundation/Ebooks/issues/" + str(github_issue_number) )



r = requests.get(image_url) # create HTTP response object
with open("cover_image.jpg",'wb') as f: 
    f.write(r.content)

send_image_to_telegram("./cover_image.jpg")

telegram_content = url + "\n\n" + book_title + " - " + category + " - " + author + "\n\n" + "உரிமை – கிரியேட்டிவ் காமன்ஸ். எல்லாரும் படிக்கலாம், பகிரலாம்.\n\n"
send_text_to_telegram(telegram_content)


os.system("date")
