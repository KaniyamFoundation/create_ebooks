# create_ebooks

This is a project to make ebooks for FreeTamilEbooks.com using LibreOffice.
This gives the ebooks in 4 formats. A4 PDF, 6 inch PDF, epub and mobi

# config.yaml

Fill the following details in the file config.yaml

```
book_title : 
book_title_in_english : 
author : 
author_mail : 
cover_image : 
artist : 
artist_email : 
ebook_maker : 
ebook_maker_email : 
license : 
content : 
category : 
```




example :

```
book_title : தசாவதாரம்
book_title_in_english : dasavatharam
author : அறிஞர் அண்ணா
author_mail : 
cover_image : dasavatharam.jpg
artist : த. சீனிவாசன்
artist_email : tshrinivasan@gmail.com
ebook_maker : த. சீனிவாசன்
ebook_maker_email : tshrinivasan@gmail.com
license : Public Domain - CC0 
content : content.odt
category : சிறுகதைகள்
```






Keep the cover image in the same parent folder.


# Installation

It needs a ubuntu linux computer.


run the below commands

```
sudo apt-get install git python3 python3-pip python3-setuptools  libreoffice-script-provider-python calibre sigil 
sudo pip3 install internetarchive pyyaml
sudo pip3 install Mastodon.py
sudo pip3 install mailjet_rest python-wordpress-xmlrpc selenium PyGithub

```






open the "fonts" directory.
Click every font.
Install all the fonts.



# Configure internet Archive Credentials


run the below command
```
ia configure
```

it will ask for your internet archive (archive.org) username and password.
Give the detais.



# ~/.config/fte-login.yaml 

Create the above file with below content

```
username :
password :

git_username :
git_password :

android_push_Authorization : 

mastodon_access_token :
mastodon_url :

mailjet_api_key :
mailjet_api_secret :

telegram_token : 
telegram_channel_chat_id : 

```

# How to Execute?



1. Open Libreoffice writer
2. Paste the content
3. Mark all Heading 1, Heading 2, Heading 3
4. Paste the cover image in the first page
5. Insert Table of Contents in 2nd or 3rd page
6. Enter Contributor, License, Publisher info on the page 2 or 3
7. Run 

```
python3 create-ebooks.py
```

This will make the ebooks and store in a new folder as "ebookname"-upload



then will upload the ebooks to archive.org site



# Changelog
* Added PDF/A export to A4 PDF and 6 inch PDF to create searchable PDF files
* Added "upload all the odt, docx files used" to archive.org
* added PyGithub Support to close the github issue automatically. - Run 'sudo pip3 install PyGithub' to install it. On Publish script add -issue <github issue number> to add a comment and close on the book is released.
* Added a filename check on book-info.yaml
* updated selenium code
