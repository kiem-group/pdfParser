import json
import urllib
from urllib.request import urlopen


# Publication resources with API https://guides.temple.edu/APIs


# Google books
def query_google_books(refs):
    print("Searching for references using Google books API:", len(refs))
    api = "https://www.googleapis.com/books/v1/volumes?q="
    for ref in refs:
        print("Ref", ref)
        url = api + urllib.parse.quote(ref)
        print("URL", url)
        resp = urlopen(url)
        book_data = json.load(resp)
        print(book_data)


# CrossRef
def query_cross_ref(refs):
    print("Searching for references using CrossRef API:", len(refs))
    from crossref.restful import Works
    works = Works()
    for ref in refs:
        print(ref)
        pub = works.query(bibliographic=ref)
        for item in pub:
            print(item['author'], item['title'])
        print("\n")