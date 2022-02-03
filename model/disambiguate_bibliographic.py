from dataclasses import dataclass
from dataclasses_json import dataclass_json
import json
from urllib.request import Request, urlopen
from urllib.parse import quote
from crossref.restful import Works
import Levenshtein
from model.publication_external import ExternalPublication
from model.industry_identifier import IndustryIdentifier
from model.contributor import Contributor
from model.reference_bibliographic import Reference
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode


def get_brill_catalogue_refs():
    bibtex_file = open('../data_test/Brill_CLS_books.bib', 'r', encoding="utf-8")
    parser = BibTexParser()
    parser.customization = convert_to_unicode
    bib_database = bibtexparser.load(bibtex_file, parser=parser)
    bibtex_file.close()
    return bib_database.get_entry_list()


@dataclass_json
@dataclass
class DisambiguateBibliographic:

    # Google books
    @classmethod
    def find_google_books(cls, ref: Reference, threshold: float = 0.75):
        if ref is None or ref.text is None:
            return
        term = ref.text if ref.title is None else ref.title
        ext = "&intitle:" + quote(ref.title) if ref.title is not None else ""
        book_data = cls.query_google_books(term, ext)
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
                            ext_pub.url = items[0]["selfLink"]
                            ext_pub.type = "google"
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

    # CrossRef
    @classmethod
    def find_crossref(cls, ref: Reference, threshold: float = 0.75):
        if ref is None or ref.text is None:
            return
        res = cls.query_crossref_pub(ref.text)
        if res is not None and ("title" in res):
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
                        ext_pub.url = res["URL"]
                        ext_pub.type = "crossref"
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

    # Brill catalogue
    @classmethod
    def find_brill(cls, ref: Reference, threshold: float = 0.75):
        if ref.title:
            ratio_max = 0
            res = None
            # TODO refactor to load once per class
            bib_database_refs = get_brill_catalogue_refs()
            for entry in bib_database_refs:
                ratio_entry = 0
                if "title" in entry.keys():
                    ratio_entry = Levenshtein.ratio(entry["title"], ref.title)
                    if "author" in entry.keys():
                        ratio_author = Levenshtein.ratio(entry["author"], ref.author)
                        if ratio_entry + ratio_author > 2 * ratio_entry:
                            ratio_entry = (ratio_entry + ratio_author) / 2
                if ratio_entry > ratio_max:
                    ratio_max = ratio_entry
                if ratio_max >= threshold:
                    res = entry
            if res is not None:
                if ref.refers_to is None:
                    ref.refers_to = []
                    ext_pub = ExternalPublication(confidence=ratio_max, title=res["title"], publisher="Brill", type="brill")
                    if "author" in res:
                        ext_pub.authors = res["author"]
                    if "address" in res:
                        ext_pub.location = res["address"]
                    if "year" in res:
                        ext_pub.year = res["year"]
                    if "url" in res:
                        ext_pub.url = res["url"]
                    ext_pub.identifiers = []
                    if "doi" in res:
                        ext_pub.identifiers.append(IndustryIdentifier(res["doi"], "doi", ""))
                    if "isbn" in res:
                        ext_pub.identifiers.append(IndustryIdentifier(res["isbn"], "isbn", ""))
                    ref.refers_to.append(ext_pub)

    @classmethod
    def query_google_books(cls, ref: str, ext: str = ""):
        url = "https://www.googleapis.com/books/v1/volumes?q=" + quote(ref) + ext
        resp = urlopen(url)
        book_data = json.load(resp)
        return book_data

    @classmethod
    def query_crossref_pub(cls, ref: str):
        works = Works()
        res = works.query(bibliographic=ref)
        for item in res:
            return item

    @classmethod
    def query_open_citations(cls, doi: str) -> json:
        url = "https://opencitations.net/index/coci/api/v1/citations/" + doi
        req = Request(url, headers={'User-Agent': 'Chrome/93.4'})
        resp = urlopen(req)
        book_data = json.load(resp)
        return book_data

    # Publication knowledge bases with API https://guides.temple.edu/APIs

    # DataCite