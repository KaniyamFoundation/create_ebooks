
### run this first
# soffice --invisible "-accept=socket,host=localhost,port=8100,tcpNoDelay=1;urp;" &


# Fill in TextFields                                                                            
                                                                                                
import uno                                                                                      
import unohelper                                                                                
import string                                                                                   
import yaml
import os
import re
import sys
import time
import glob


os.system("clear")

print("Processing the config file")




book_info = yaml.load(open('book-info.yaml'))

book_title = book_info['book_title']
book_title_in_english = book_info['book_title_in_english'].replace(" ","_").replace("-","_")
author = book_info['author']

if book_info['author_mail']:
    author_mail = book_info['author_mail']
else:
    author_mail = " "

cover_image = book_info['cover_image']



if book_info['artist']:
    artist = book_info['artist']
else:
    artist = " " 

if book_info['artist_email']:
    artist_email = book_info['artist_email']
else:
    artist_email = " " 

if book_info['translator']:
    translator = book_info['translator']
else:
    translator = " " 

if book_info['translator_email']:
    translator_email = book_info['translator_email']
else:
    translator_email = " " 


ebook_maker = book_info['ebook_maker']
ebook_maker_email = book_info['ebook_maker_email']
license = book_info['license']
category = book_info['category']
content = book_info['content']


if not os.path.isfile(cover_image):
    print("Found issue with cover image in book-info.yaml. Check the filename")
    sys.exit()


if not os.path.isfile(content):
    print("Found issue with content file name in book-info.yaml. Check the filename")
    sys.exit()




if not category:
    print("Enter Category in book-info.yaml")
    sys.exit()

    
if not license:
    print("Enter License in book-info.yaml")
    sys.exit()


if not author:
    print("Enter Author in book-info.yaml")
    sys.exit()

if not ebook_maker:
    print("Enter Ebook Maker in book-info.yaml")
    sys.exit()

if not ebook_maker_email:
    print("Enter Ebook Maker Email in book-info.yaml")
    sys.exit()




os.system('soffice --invisible "--accept=socket,host=localhost,port=8100,tcpNoDelay=1;urp;" &')
time.sleep(5)


print("Processing " +book_title_in_english)


cwd = os.getcwd()

print("Converting to A4 odt")

# a UNO struct later needed to create a document                                                
from com.sun.star.beans import PropertyValue                                                    
                                                                                                
localContext = uno.getComponentContext()                                                        
                                                                                                
resolver = localContext.ServiceManager.createInstanceWithContext(                               
                "com.sun.star.bridge.UnoUrlResolver", localContext )                            
                                                                                                
smgr = resolver.resolve( "uno:socket,host=localhost,port=8100;urp;StarOffice.ServiceManager" )  
remoteContext = smgr.getPropertyValue( "DefaultContext" )                                       
desktop = smgr.createInstanceWithContext( "com.sun.star.frame.Desktop",remoteContext)           
                                                                                                
# Open the document                                                                             
hidden = PropertyValue( "Hidden" , 0 , True, 0 ),                                               
                                                                                                
source_file_url = "file://" + cwd + "/" + content
a4_template = "file://" + cwd + "/templates/fte-template.ott"
six_inch_template = "file://" + cwd + "/templates/fte-6-inch-template.ott"

document = desktop.loadComponentFromURL(source_file_url ,"_blank", 0, (hidden))

# https://forum.openoffice.org/en/forum/viewtopic.php?f=7&t=78689

styles = document.StyleFamilies
styles.loadStylesFromURL(a4_template, styles.StyleLoaderOptions)

document.refresh()
indexes = document.getDocumentIndexes()
indexes.getByIndex(0).Title = ""
indexes.getByIndex(0).Title = "பொருளடக்கம்"
indexes.getByIndex(0).update()



a4_odt = "file://" + cwd + "/" + book_title_in_english + "_a4.odt" 
document.storeAsURL(a4_odt,())
print("Done.")    


print("Saving as A4 PDF")
a4_pdf = "file://" + cwd + "/" + book_title_in_english + "_a4.pdf"


# filter data
fdata = []
fdata1 = PropertyValue()
fdata1.Name = "SelectPdfVersion"
fdata1.Value = 2
fdata2 = PropertyValue()
fdata2.Name = "Quality"
fdata2.Value = 100
fdata.append(fdata1)
fdata.append(fdata2)

args = []
arg1 = PropertyValue()
arg1.Name = "FilterName"
arg1.Value = "writer_pdf_Export"
arg2 = PropertyValue()
arg2.Name = "FilterData"
arg2.Value = uno.Any("[]com.sun.star.beans.PropertyValue", tuple(fdata) )
args.append(arg1)
args.append(arg2)

document.storeToURL(a4_pdf, tuple(args))
print("Done.")



print("Converting as 6 inch odt")
styles = document.StyleFamilies
styles.loadStylesFromURL(six_inch_template, styles.StyleLoaderOptions)



graphObjs = document.GraphicObjects
for i in range(0, graphObjs.getCount()):
    graphObj = graphObjs.getByIndex(i)
    graphObj.Width = graphObj.Width/2
    graphObj.Height = graphObj.Height/2


document.refresh()
indexes = document.getDocumentIndexes()
indexes.getByIndex(0).Title = "பொருளடக்கம்"
indexes.getByIndex(0).update()


six_inch_odt = "file://" + cwd + "/" + book_title_in_english + "_6_inch.odt" 
document.storeAsURL(six_inch_odt,())
print("Done.")
    
print("Converting to 6 inch PDF")    
six_inch_pdf = "file://" + cwd + "/" + book_title_in_english + "_6_inch.pdf"

# filter data
fdata = []
fdata1 = PropertyValue()
fdata1.Name = "SelectPdfVersion"
fdata1.Value = 2
fdata2 = PropertyValue()
fdata2.Name = "Quality"
fdata2.Value = 100
fdata.append(fdata1)
fdata.append(fdata2)

args = []
arg1 = PropertyValue()
arg1.Name = "FilterName"
arg1.Value = "writer_pdf_Export"
arg2 = PropertyValue()
arg2.Name = "FilterData"
arg2.Value = uno.Any("[]com.sun.star.beans.PropertyValue", tuple(fdata) )
args.append(arg1)
args.append(arg2)


document.storeToURL(six_inch_pdf, tuple(args))
print("Done.")


print("Converting to epub")
epub_command = "ebook-convert " + book_title_in_english + "_a4.odt" + " " + book_title_in_english + ".epub" + \
                " --pretty-print   --level1-toc //h:h1  --level2-toc //h:h2  " + \
                " --authors '" + author +  "' --language Tamil --publisher FreeTamilEbooks.com " + \
                " --title '" + book_title +"' >  epub.log 2>&1"


os.system(epub_command)
print("Done.")

print("Converting to mobi")
mobi_command = "ebook-convert " + book_title_in_english + ".epub " + book_title_in_english + ".mobi " + ">  mobi.log 2>&1 "

os.system(mobi_command)
print("Done.")

print("Convertion Completed. Check the Books now")

os.system("killall -9 soffice.bin")

f = open("_rules.conf","w")
f.write("CAT.ALL")
f.close()



while True:
    try:
        answer = input("Are the books ready to upload Y/N ? : ")

        if answer.lower() == 'n':
            print("Fix the errors and run the script again. Thanks.")
            break
            sys.exit()

        elif answer.lower() == 'y':

            os.mkdir(book_title_in_english + "-upload")
            os.system("mv *pdf *odt *doc *docx *epub *mobi *jpg *png *JPG *PNG " + book_title_in_english + "-upload 2>/dev/null" )
            os.system("cp *.yaml *.conf " + book_title_in_english + "-upload" )

            timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

            ia_identifier = book_title_in_english + "-" + timestamp

            content_dir = book_title_in_english + "-upload/"


            ia_upload = "ia upload " + ia_identifier + \
            " -m collection:opensource -m mediatype:texts -m sponsor:FreeTamilEbooks -m language:tam "


            all_files = glob.glob(content_dir + "*")

            for afile in all_files:
                ia_upload = ia_upload  +  "'" + afile + "'" +  " "


            print("Uploading to Internet Archive")
            print(ia_upload)
            os.system(ia_upload)


            print("Uploaded to https://archive.org/details/" + ia_identifier)
            break
        else:
            raise ValueError('Enter only Y or N')

    except ValueError:
       print("Enter only Y or N")


