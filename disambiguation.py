import json
from urllib.request import Request, urlopen
from urllib.parse import quote
from crossref.restful import Works
import Levenshtein

# Publication resources with API https://guides.temple.edu/APIs


# Google books
def disambiguate_google_books(ref, threshold = 0.75):
    if ref is None or ref.text is None:
        return
    term = ref.text if ref.title is None else ref.title
    ext = "&intitle:" + quote(ref.title) if ref.title is not None else ""
    book_data = query_google_books(term, ext)
    if "items" in book_data:
        items = book_data["items"]
        if len(items) >= 0:
            if "volumeInfo" in items[0]:
                google_title = items[0]["volumeInfo"]["title"]
                ratio = Levenshtein.ratio(ref.title, google_title)
                if ratio > threshold:
                    if "selfLink" in items[0]:
                        ref.url_google = items[0]["selfLink"]
                    if "industryIdentifiers" in items[0]["volumeInfo"]:
                        ref.industry_identifiers = json.dumps(items[0]["volumeInfo"]["industryIdentifiers"])
                    # TODO: override parsed contributors, title, publication year

def query_google_books(ref, ext=""):
    url = "https://www.googleapis.com/books/v1/volumes?q=" + quote(ref) + ext
    resp = urlopen(url)
    book_data = json.load(resp)
    return book_data


# CrossRef
def disambiguate_crossref(ref, threshold=0.75):
    if ref is None or ref.text is None:
        return
    res = query_crossref_pub(ref.text)
    if "title" in res:
        if len(res["title"]) > 0:
            ratio = Levenshtein.ratio(ref.title, res["title"][0])
            if ratio >= threshold:
                if "DOI" in res:
                    ref.doi = res["DOI"]
                if "ISBN" in res:
                    ref.isbn = res["ISBN"]
                if "URL" in res:
                    ref.url_crossref = res["URL"]
                # TODO: override parsed contributors, title, publication year


def query_crossref_pub(ref):
    works = Works()
    res = works.query(bibliographic=ref)
    for item in res:
        return item


def disambiguate_open_citations(ref):
    if ref is None or ref.title is None:
        return
    res = query_open_citations(ref.title)


def query_open_citations(ref):
    url = "https://opencitations.net/api/v1/require/doi&filter=" + "title:" + quote(ref)
    print(url)
    # url = "https://opencitations.net/api/v1/metadata/10.1108/jd-12-2013-0166__10.1016/j.websem.2012.08.001"
    req = Request(url, headers={'User-Agent': 'Chrome/93.4'})
    resp = urlopen(req)
    book_data = json.load(resp)
    return book_data

