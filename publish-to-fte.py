# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options


from wordpress_xmlrpc import WordPressPost
from wordpress_xmlrpc import Client
from wordpress_xmlrpc.methods import posts,media
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import taxonomies

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

from mastodon import Mastodon
#from mailjet_rest import Client
import mailjet_rest

parser = argparse.ArgumentParser()

parser.add_argument('-l','--local-file', help='Use Local File', required=False)
parser.add_argument('-r','--remote-book-url', help='Use Remote File', required=False)
parser.add_argument('-i','--interactive', help='Interactive Mode', required=False)
parser.add_argument('-bn','--book_number', help='Book Number', required=True)


args = parser.parse_args()

local_file = args.local_file
remote_book_url = args.remote_book_url
interactive = args.interactive
book_number = args.book_number


home = os.getenv("HOME")

fte_yaml = yaml.load(open(home + '/.config/fte-login.yaml'))

fte_username = fte_yaml['username']
fte_password = fte_yaml['password']

git_username = fte_yaml['git_username']
git_password = fte_yaml['git_password']


android_push_Authorization = fte_yaml['android_push_Authorization']


mastodon_access_token = fte_yaml['mastodon_access_token']
mastodon_url = fte_yaml['mastodon_url']


mailjet_api_key = fte_yaml['mailjet_api_key']
mailjet_api_secret = fte_yaml['mailjet_api_secret']



if remote_book_url:
    book_url = remote_book_url


    print("Getting Book Info")
    book_info = yaml.load(urlopen(book_url.replace('details','download') + '/book-info.yaml'))


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
        author_mail = " "

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



    ebook_maker = book_info['ebook_maker']
    ebook_maker_email = book_info['ebook_maker_email']
    license = book_info['license']




    epub_url = book_url.replace('details','download') + "/" +  book_title_in_english + ".epub"
    mobi_url = book_url.replace('details','download') + "/" +  book_title_in_english + ".mobi"
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
    mobi_url = input("Mobi URL : ").strip()
    a4_pdf_url  = input("A4 PDF URL : ").strip()
    six_inch_pdf_url = input("Six inch PDF URL : ")
    
    cover_image = book_title_in_english + "_cover.jpg"



print("Logging in to FreeTamilEbooks.com")
#binary = FirefoxBinary('/home/shrinivasan/firefox/firefox')
#driver = webdriver.Firefox(firefox_binary=binary)

options = Options()
# options.headless = True  # older webdriver versions
options.set_headless(True) # newer webdriver versions

driver = webdriver.Firefox(options=options,executable_path=r'./geckodriver')
#driver = webdriver.Firefox(executable_path=r'./geckodriver')

driver.implicitly_wait(5)
driver.maximize_window()
base_url = "http://freetamilebooks.com"
verificationErrors = []
accept_next_alert = True





driver.get("http://freetamilebooks.com/wp-login.php?redirect_to=http%3A%2F%2Ffreetamilebooks.com%2Fwp-admin%2Fpost-new.php%3Fpost_type%3Ddlm_download&reauth=1&jetpack-sso-show-default-form=1")
driver.implicitly_wait(5)
       # driver.find_element_by_link_text("Log in with username and password").click()
driver.find_element_by_id("user_pass").clear()
driver.find_element_by_id("user_pass").send_keys(fte_password)
driver.find_element_by_id("user_login").clear()
driver.find_element_by_id("user_login").send_keys(fte_username)
driver.find_element_by_id("wp-submit").click()
      #  driver.find_element_by_link_text("Download").click()
driver.implicitly_wait(20)




def add_download(filename,file_url):
    driver.get("http://freetamilebooks.com/wp-admin/post-new.php?post_type=dlm_download")
    driver.find_element_by_id("title").clear()
    driver.find_element_by_id("title").send_keys(filename)
    driver.find_element_by_xpath(".//*[@class='button plus add_file']").click()
#    driver.implicitly_wait(30)
    time.sleep(20)
      #  driver.find_element_by_xpath(".//*[@class='downloadable_file_urls']").click()
    driver.find_element_by_xpath(".//*[@class='downloadable_file_urls']").send_keys(file_url)
#    driver.implicitly_wait(30)
    time.sleep(20)
    publish_button = WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.XPATH,  ".//*[@id='publish']"))
    )
    publish_button.click()
#    driver.find_element_by_xpath(".//*[@id='publish']").click()
#    driver.implicitly_wait(30)
    time.sleep(20)
 
 
    dl_text  = WebDriverWait(driver, 40).until(
        EC.presence_of_element_located((By.ID,  "dlm-info-id"))
    )
    dl_id  = dl_text.get_attribute('value')
 
   # dl_id = driver.find_element_by_id('dlm-info-id').get_attribute('value')
#    driver.implicitly_wait(30)
    time.sleep(20)
    dl_url = driver.find_element_by_id('dlm-info-url').get_attribute('value')
    print("Adding " + filename)
    return(dl_id,dl_url)

    
    
print("Adding Downloads")    
epub_data = add_download(book_title + " epub",epub_url )
mobi_data = add_download(book_title + " mobi",mobi_url)
a4_pdf_data = add_download(book_title + " A4 PDF",a4_pdf_url)
six_inch_pdf_data = add_download(book_title + " 6 inch PDF",six_inch_pdf_url)
driver.quit()

#epub_data = (1,"a")
#mobi_data = (1,"a")
#a4_pdf_data = (1,"a")
#six_inch_pdf_data = (1,"a")

#print(book_title_in_english)
 
#For security, consider creating a user just for your script.


wp = Client('http://freetamilebooks.com/xmlrpc.php', fte_username, fte_password)
post = WordPressPost()


taxes = wp.call(taxonomies.GetTaxonomies())
#print(taxes)


 
with urllib.request.urlopen(cover_url) as response, open(cover_image, 'wb') as out_file:
    shutil.copyfileobj(response, out_file)
#print("Downloaded Cover Image")    
    
filename = cover_image


data = {
        'name': filename,
        'type': 'image/jpeg',  # mimetype
}


# read the binary file and let the XMLRPC library encode it into base64
with open(filename, 'rb') as img:
        data['bits'] = xmlrpc_client.Binary(img.read())
        

response = wp.call(media.UploadFile(data))
#print(response)

image_url = response["url"]

attachment_id = response['id']

#print("Uploaded cover Image")

medium_image_width = str(response["metadata"]["sizes"]["medium"]["width"])
medium_image_height = str(response["metadata"]["sizes"]["medium"]["height"])

medium_image_url = image_url.replace('.jpg','-' + str(medium_image_width) +'x' + str(medium_image_height) + '.jpg')

content = "நூல் : " +  book_title + "\n\n" + "ஆசிரியர் : " + author + "\n\n" +    "<a href=" + image_url + "><img class='alignright size-medium wp-image-6958' src=" + medium_image_url + "  width='" + medium_image_width + "' height='" + medium_image_height +"' /></a>" + "\n" 


print("Generating Content to Post")

if author_mail :
    content = content + "மின்னஞ்சல் : " + author_mail + "\n\n"


if artist:
    content = content + "அட்டைப்படம் : " + artist + "\n\n"

if artist_email:
    content = content + artist_email + "\n\n"


if translator:
    content =  content + "தமிழாக்கம் : " + translator + "\n\n"

if translator_email:
    content = content + translator_email + "\n\n"
    
if ebook_maker:
    content = content + "மின்னூலாக்கம் : " + ebook_maker + "\n"

if ebook_maker_email:
    content = content + "மின்னஞ்சல் : " + ebook_maker_email + "\n\n"

content = content + "வெளியிடு : FreeTamilEbooks.com" + "\n\n"
content = content + "உரிமை : " + license + "\n\n" + "உரிமை – கிரியேட்டிவ் காமன்ஸ். எல்லாரும் படிக்கலாம், பகிரலாம்." + "\n"



extra = '''

&nbsp;

&nbsp;

&nbsp;

<b>பதிவிறக்க*</b>

ஆன்ட்ராய்டு(FBreader), ஆப்பிள், புது நூக் கருவிகளில் படிக்க

[download id=" ''' + str(epub_data[0]) + '''" template="button"]

புது கிண்டில் கருவிகளில் படிக்க

[download id=" ''' + str(mobi_data[0]) + '''" template="button"]

குனூ/லினக்ஸ், விண்டோஸ் கணிணிகளில் படிக்க

[download id=" ''' + str(a4_pdf_data[0]) + '''" template="button"]

பழைய கிண்டில்,நூக் கருவிகளில் படிக்க

[download id=" ''' + str(six_inch_pdf_data[0]) + '''" template="button"]

&nbsp;

&nbsp;

&nbsp;


<a>Send To Kindle Directly</a><a href="http://35.166.185.40/send2kindle?fileurl=''' + str(mobi_data[1]) + '''&amp;filename=''' +book_title_in_english + '''.mobi" target="_blank" rel="noopener"><img class="alignleft wp-image-6127 " src="http://freetamilebooks.com/wp-content/uploads/2017/09/send-to-kindle-logo.jpg" alt="" width="579" height="129" /></a>

&nbsp;

&nbsp;

&nbsp;

பிற வடிவங்களில் படிக்க  – ''' + book_url + '''


புத்தக எண் - ''' + str(book_number) + '''


'''

print("Publising the Ebook")  
content = content + extra

post.title = book_title + " - " + category + " - " + author
post.slug = book_title_in_english
post.post_type = 'ebooks'

post.content = content

post.thumbnail = attachment_id
post.comment_status = 'open'

post.post_status = 'publish'
#post.post_status = 'draft'


if artist:
    post.terms_names = {
    'genres': [category],
    'contributors': [artist, ebook_maker],
    'authors' : [author]
    }
    
else:
    post.terms_names = {
    'genres': [category],
    'contributors': [ebook_maker],
    'authors' : [author]
    }
    

wp.call(NewPost(post))

print("Published")


os.system("rm " + cover_image)


book_name = book_title
bookid = str(uuid.uuid4())
cover_image = image_url
gen = category
epub_link = epub_data[1]
authors = author
url =   "http://freetamilebooks.com/ebooks/" + book_title_in_english



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

if len(author_mail.strip()) > 2:


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



