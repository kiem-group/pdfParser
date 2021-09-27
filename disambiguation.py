import json
from urllib.request import urlopen
from urllib.parse import quote
from crossref.restful import Works

# Publication resources with API https://guides.temple.edu/APIs

# Google books
def query_google_books(refs):
    for ref in refs:
        print("Ref", ref)
        book_data = query_google_book(ref)
        print(book_data)


def query_google_book(ref, ext):
    api = "https://www.googleapis.com/books/v1/volumes?q="
    url = api + quote(ref) + ext
    # print("URL", url)
    resp = urlopen(url)
    book_data = json.load(resp)
    return book_data


# CrossRef
def query_crossref_pubs(refs):
    print("Searching for references using CrossRef API:", len(refs))
    from crossref.restful import Works
    works = Works()
    for ref in refs:
        print(ref)
        pub = works.query(bibliographic=ref)
        for item in pub:
            print(item['author'], item['title'])
        print("\n")


def query_crossref_pub(ref):
    works = Works()
    res = works.query(bibliographic=ref)
    for item in res:
        return item
