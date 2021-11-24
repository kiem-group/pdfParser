import json
from urllib.request import Request, urlopen
from urllib.parse import quote
from crossref.restful import Works
import Levenshtein
from model.publication_external import ExternalPublication
from model.industry_identifier import IndustryIdentifier
from model.contributor import Contributor

# Publication resources with API https://guides.temple.edu/APIs


# Google books
def disambiguate_google_books(ref, threshold=0.75):
    if ref is None or ref.text is None:
        return
    term = ref.text if ref.title is None else ref.title
    ext = "&intitle:" + quote(ref.title) if ref.title is not None else ""
    book_data = query_google_books(term, ext)
    if "items" in book_data:
        items = book_data["items"]
        if len(items) >= 0:
            if "volumeInfo" in items[0]:
                volumeInfo = items[0]["volumeInfo"]
                google_title = volumeInfo["title"]
                ratio = Levenshtein.ratio(ref.title, google_title)
                if ratio > threshold:
                    ext_pub = ExternalPublication(confidence=ratio)
                    if "selfLink" in items[0]:
                        ext_pub.url_google = items[0]["selfLink"]
                    if "industryIdentifiers" in volumeInfo:
                        ext_pub.identifiers = []
                        for obj in volumeInfo["industryIdentifiers"]:
                            id_obj = IndustryIdentifier(obj["identifier"], obj["type"].lower(), "")
                            ext_pub.identifiers.append(id_obj)
                    # Extract publication details
                    ext_pub.title = google_title
                    if "authors" in volumeInfo:
                        ext_pub.authors = []
                        for author in volumeInfo["authors"]:
                            ext_pub.authors.append(Contributor(full_name=author, type="author"))
                    if "publishedDate" in volumeInfo:
                        ext_pub.year = volumeInfo["publishedDate"]
                    if "language" in volumeInfo:
                        ext_pub.lang = volumeInfo["language"]
                    # Save external publication
                    if ref.refers_to is None:
                        ref.refers_to = []
                    ref.refers_to.append(ext_pub)


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
                ext_pub = ExternalPublication(confidence=ratio)
                ext_pub.identifiers = []
                if "DOI" in res:
                    ext_pub.identifiers.append(IndustryIdentifier(res["DOI"], "doi", ""))
                if "ISBN" in res:
                    ext_pub.identifiers.append(IndustryIdentifier(res["ISBN"], "isbn", ""))
                if "URL" in res:
                    ext_pub.url_crossref = res["URL"]
                # @Example: 'published': {'date-parts': [[2001, 4]]}}
                if "published" in res:
                    if "date-parts" in res["published"]:
                        date_parts = res["published"]["date-parts"]
                        if len(date_parts) > 0:
                            if len(date_parts[0]) > 0:
                                ext_pub.year = date_parts[0][0]
                # @Example: 'author': [{'given': 'William', 'family': 'Allan', 'sequence': 'first', 'affiliation': []}]
                if "author" in res:
                    for author in res["author"]:
                        ext_pub.authors = []
                        if "family" in author and "given" in author:
                            ext_pub.authors.append(Contributor(surname=author["family"], given_names=author["given"], type="author"))
                # @Example: 'title': ['Euripides in Megale Hellas: some aspects of the early reception of tragedy'],
                if "title" in res and len(res["title"]) > 0:
                    ext_pub.title = res["title"][0]
                # @Example: 'publisher': 'Oxford University Press'
                if "publisher" in res:
                    ext_pub.publisher = res["publisher"]
                # @Example: 'language': 'en'
                if "language" in res:
                    ext_pub.lang = res["language"]
                if ref.refers_to is None:
                    ref.refers_to = []
                ref.refers_to.append(ext_pub)


def query_crossref_pub(ref):
    works = Works()
    res = works.query(bibliographic=ref)
    for item in res:
        return item


def disambiguate_open_citations(ref):
    if ref is None or ref.title is None:
        return
    res = query_open_citations(ref.title)


def query_open_citations(doi):
    url = "https://opencitations.net/index/coci/api/v1/citations/" + doi
    print(url)
    req = Request(url, headers={'User-Agent': 'Chrome/93.4'})
    resp = urlopen(req)
    book_data = json.load(resp)
    return book_data
