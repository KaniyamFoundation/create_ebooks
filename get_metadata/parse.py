import json
import sys
import traceback
#import urllib
#import urllib.parse
import html

f = open("fte.json")

data = json.load(f)

all_data = len(data)

out = open("fte-results.csv","w")
counter = 0
for book in data:

    book_id = book['id']
    slug = link = title = genres = authors = content = epub_link = epub_id = mobi_link = mobi_id = a4_pdf_link = a4_pdf_id = six_inch_pdf_link = six_inch_pdf_id = ""
    print(counter)
    slug = book['slug']
    link = book['link']
    full_title = book['title']['rendered']  #fix the url encoding
    full_title_uni = html.unescape(full_title)
    title = full_title_uni
    
    genres_list = []
    authors_list = []
    genres_array = book['genres'] #multi
    authors_array = book['authors'] #multi
    for i in genres_array:
        genres_list.append(str(i))
    for j in authors_array:
        authors_list.append(str(j))

    genres = ' '.join(genres_list)
    authors = ' '.join(authors_list)


    
    if full_title_uni.count("–") == 2:
        authors = full_title_uni.split("–")[-1]
        genres = full_title_uni.split("–")[-2]
        title = full_title_uni.split("–")[0]

        
        
    
    if full_title_uni.count("–") == 1:        
        authors = full_title_uni.split("–")[-1]
        title = full_title_uni.split("–")[0]
    
    '''
    print(slug)
    print(link)
    print(title)

    print(genres)
    print(authors)
    '''
    
    try:
        content = book['content']['rendered']

        if "நூல் : " in content:
            title = content.split("நூல் : ")[1].split("\n")[0].split("<")[0]
            title = html.unescape(title)
        if "ஆசிரியர் : " in content:
            authors = content.split("ஆசிரியர் : ")[1].split("\n")[0].split("<")[0]

    

        #author = content.split('ஆசிரியர் : ')[1].split("<br />")[0]
        if ("ஆப்பிள், புது நூக் கருவிகளில் படிக்க") in content:
            epub_link = "https://" + content.split("ஆப்பிள், புது நூக் கருவிகளில் படிக்க")[1].split('href=')[1].split("rel=")[0].replace('"','').split("https://")[1].split("/?")[0]
#
        #epub_link = content.split("-epub")[0].split("
            epub_id = content.split("ஆப்பிள், புது நூக் கருவிகளில் படிக்க")[1].split("id=")[1].split(">\n")[0].split("-")[-1].replace('"','').replace(">",'')

        if ("புது கிண்டில் கருவிகளில் படிக்க") in content:
            mobi_link ="https://" +  content.split("புது கிண்டில் கருவிகளில் படிக்க")[1].split('href=')[1].split("rel=")[0].replace('"','').split("https://")[1].split("/?")[0]
            mobi_id = content.split("புது கிண்டில் கருவிகளில் படிக்க")[1].split("id=")[1].split(">\n")[0].split("-")[-1].replace('"','').replace(">",'')

        if ("கணிணிகளில் படிக்க") in content:
            a4_pdf_link = "https://" + content.split("கணிணிகளில் படிக்க")[1].split('class="download-link')[1].split('href')[1].split("rel=")[0].replace('"','').split("https://")[1].split("/?")[0]
            a4_pdf_id = content.split("கணிணிகளில் படிக்க")[1].split("id=")[1].split(">\n")[0].split("-")[-1].replace('"','').replace(">",'')

        if "பழைய கிண்டில்,நூக் கருவிகளில் படிக்க" in content:
            six_inch_pdf_link ="https://" +  content.split("பழைய கிண்டில்,நூக் கருவிகளில் படிக்க")[1].split('href=')[1].split("rel=")[0].replace('"','').split("https://")[1].split("/?")[0]
            six_inch_pdf_id = content.split("பழைய கிண்டில்,நூக் கருவிகளில் படிக்க")[1].split("id=")[1].split(">\n")[0].split("-")[-1].replace('"','').replace(">",'')

        #print(author)
        '''
        print(epub_link)
        print(epub_id)

        print(mobi_link)
        print(mobi_id)
        print(a4_pdf_link)
        print(a4_pdf_id)
        print("a4 id = " + str(a4_pdf_id))
        print("6 inch link = " + six_inch_pdf_link)
        print("6 inch id = " + str(six_inch_pdf_id))
        
        print("\n\n========\n\n")
        '''
        counter = counter +1

        #print(str(counter) + "~" + slug +"~" + link +"~" + title +"~" + genres +"~" + authors   )

              
        csv_content = (str(counter) + "~" + str(book_id) + "~" + slug +"~" + link +"~" + title +"~" + genres +"~" + authors +"~"  + epub_link +"~" + epub_id +"~" + mobi_link +"~" + mobi_id +"~" + a4_pdf_link +"~" + a4_pdf_id +"~" + str(six_inch_pdf_link) +"~" + six_inch_pdf_id + "\n")
        #print(csv_content)
        out.write(csv_content)
    #out.close()
        
#        sys.exit()
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print(content)
        sys.exit()
        #a4_pdf_link = content.split("கணிணிகளில் படிக்க")[1].split('href=')[1].split("rel=")[0].replace('"','').split("https://")[1].split("/?")[0]
        a4_pdf_link = content.split("கணிணிகளில் படிக்க")[1].split('href=')[1]
        print(a4_pdf_link)
        
        traceback_text = traceback.format_exc()

        err = open("err.txt","w")
        err.write(str(counter))
        err.write(link)
        err.write(content)
        err.write("=======\n\n")
