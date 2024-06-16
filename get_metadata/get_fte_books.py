import sys
import os
import time

counter = 1
import csv
with open('fte_metadata.csv', mode ='r') as file:    
    csvFile = csv.DictReader(file,delimiter="~")
       
             
    for book in csvFile:
        print("Downloading book number : " + str(counter))
        counter = counter +1
        print(book['book_name_tamil'])

        filename = book['book_name_tamil'].strip() +"--"+ book['author'].strip() + "--" + book['genre'].strip()

        wget_command = "wget -q -O '" + filename + ".epub' " + book['epub_url']
        print(wget_command)
        os.system(wget_command)

        convert = "pandoc -f epub -t plain -o '"  + filename + ".txt'  '" +  filename + ".epub'"
        print(convert)
        os.system(convert)

        os.system("rm '" + filename + ".epub'")
        time.sleep(5)

