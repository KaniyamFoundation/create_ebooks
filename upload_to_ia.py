import string
import yaml
import os
import re
import sys
import time
import glob

book_info = yaml.load(open('book-info.yaml'))

book_title = book_info['book_title']
book_title_in_english = book_info['book_title_in_english'].replace(" ","_").replace("-","_")
cover_image = book_info['cover_image']

epubfile = book_title_in_english + ".epub"
mobifile = book_title_in_english + ".mobi"
a4_pdf = book_title_in_english + "_a4.pdf"
six_inch_file = book_title_in_english + "_6_inch.pdf"


if os.path.isfile(epubfile) == False:
    print("File name error in epub file. Change as " + epubfile)
    sys.exit()

if os.path.isfile(mobifile) == False:
    print("File name error in mobi file. Change as " + mobifile)
    sys.exit()

if os.path.isfile(a4_pdf) == False:
    print("File name error in A4 PDF file. Change as " + a4_pdf)
    sys.exit()

if os.path.isfile(six_inch_file) == False:
    print("File name error in 6 inch PDF file. Change as " + six_inch_file)
    sys.exit()


if os.path.isfile(cover_image) == False:
    print("File name error in Cover Image. Change as " + cover_image)
    sys.exit()


os.mkdir(book_title_in_english + "-upload")
os.system("mv *pdf *odt *doc *docx *epub *mobi *jpg *png *JPG *PNG " + book_title_in_english + "-upload 2>/dev/null" )
os.system("cp *.yaml " + book_title_in_english + "-upload" )
os.system("cp *.conf " + book_title_in_english + "-upload" )

timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

ia_identifier = book_title_in_english + "-" + timestamp

content_dir = book_title_in_english + "-upload/"

ia_upload = "ia upload " + ia_identifier + \
" -m collection:opensource -m mediatype:texts -m sponsor:FreeTamilEbooks -m language:tam "


all_files = glob.glob(content_dir + "*")

for afile in all_files:
    ia_upload = ia_upload  +  "'" + afile + "'" +  " "


'''
ia_upload = "ia upload " + ia_identifier + \
" -m collection:opensource -m mediatype:texts -m sponsor:FreeTamilEbooks -m language:tam " +  \
content_dir + book_title_in_english + ".epub " + content_dir + book_title_in_english + ".mobi " +\
content_dir + book_title_in_english + "_a4.pdf " + content_dir + book_title_in_english + "_6_inch.pdf " + \
content_dir + cover_image + " "  + "book-info.yaml" + " _rules.conf"
'''

print("Uploading to Internet Archive")
print(ia_upload)
os.system(ia_upload)


print("Uploaded to https://archive.org/details/" + ia_identifier)

