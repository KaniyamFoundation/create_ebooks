import requests
import json
import sys
import time

def read_wordpress_posts():
    api_url = 'https://freetamilebooks.com/wp-json/wp/v2/ebooks'
    response = requests.get(api_url)
    response_json = response.json()
    print(response_json)


def get_total_pagecount():
    api_url = 'https://freetamilebooks.com/wp-json/wp/v2/ebooks?page=1&per_page=100'
    response = requests.get(api_url)
    pages_count = response.headers['X-WP-TotalPages']
    return int(pages_count)

#print(get_total_pagecount())

#all_ebooks = read_wordpress_posts()
#print((all_ebooks))


def read_wordpress_post_with_pagination():
    total_pages = get_total_pagecount()
    current_page = 1
    all_page_items_json = []
    while current_page <= total_pages:
        api_url = f"https://freetamilebooks.com/wp-json/wp/v2/ebooks?page={current_page}&per_page=100"
        page_items = requests.get(api_url)
        page_items_json = page_items.json()
        all_page_items_json.extend(page_items_json)
        current_page = current_page + 1
        time.sleep(5)
    return all_page_items_json


'''
all_data = read_wordpress_post_with_pagination()

print(all_data)
with open("result.json","w",encoding='utf8') as out:
    out.write(json.dumps(all_data))
    json.dump(all_data,out,ensure_ascii=False)
#out.close()

#with open('filename', 'w', encoding='utf8') as json_file:
#    json.dump("ברי צקלה", json_file, ensure_ascii=False)
'''

import codecs
import json

inp = open("result.json","r")
data = json.load(open("result.json"))
with codecs.open('your_file.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

    
