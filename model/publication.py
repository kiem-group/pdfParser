from __future__ import annotations
from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json
from lxml import etree
import zipfile
import json
from model.reference_index import IndexReference
from model.reference_bibliographic import Reference
from model.contributor import Contributor
from model.pdf_parser import PdfParser, SkippedText
from model.industry_identifier import IndustryIdentifier
from model.publication_base import BasePublication
from model.disambiguate_bibliographic import DisambiguateBibliographic
from model.disambiguate_index import DisambiguateIndex
import uuid
import re


@dataclass_json
@dataclass(unsafe_hash=True)
class Publication(BasePublication):
    """A class for holding information about a publication"""

    # Sources
    zip_path: str = None
    jats_file: str = None
    bib_file: str = None
    index_files: [str] = None

    # Relationships
    bib_refs: [Reference] = None
    index_refs: [IndexReference] = None

    # Error logs
    bib_refs_with_errors: [str] = None
    index_refs_with_errors: [str] = None
    _bib_skipped: [SkippedText] = None
    _index_skipped: [[SkippedText]] = None

    # Parsing config
    _extract_bib: bool = False
    _extract_index: bool = False

    @classmethod
    def from_zip(cls, pub_zip: str, extract_bib: bool = False, extract_index: bool = False) -> Publication:
        # TODO generate UUIDs from archive name?
        self = cls()
        if pub_zip is not None:
            self.zip_path = pub_zip
            self._extract_bib = extract_bib
            self._extract_index = extract_index
            self.__parse_zip()
        return self

    def __parse_zip(self):
        if self.zip_path is None:
            return
        print("Publication archive is being processed:", self.zip_path)
        pub_zip = zipfile.ZipFile(self.zip_path, 'r')

        for file_name in pub_zip.namelist():
            if file_name.endswith('.xml'):
                # Publication signature will be extracted in the setter
                self.jats_file = file_name
                jats_file = pub_zip.open(file_name)
                jats_root = None
                try:
                    jats_tree = etree.parse(jats_file)
                    jats_root = jats_tree.getroot()
                except:
                    print("Failed to parse JATS file", file_name)
                if jats_root is not None:
                    self.__parse_book(jats_root)
                    self.__parse_references(jats_root, pub_zip)
                jats_file.close()
        pub_zip.close()

    def __parse_book(self, jats_root):
        if jats_root is None:
            return
        book = jats_root.xpath('//book')[0]
        lang = book.xpath('//@xml:lang', namespaces={"xml": "https://www.w3.org/XML/1998/namespace"})
        self.lang = lang[0] if len(lang) > 0 else None
        self.identifiers = []
        issn = book.xpath('.//issn')
        if len(issn) > 0:
            pub_format = issn[0].xpath('/@publication-format')
            pub_id = issn[0].xpath("text()")
            self.identifiers.append(IndustryIdentifier(pub_id, "issn", pub_format))
        doi = book.xpath('.//book-meta/book-id[@book-id-type="doi"]')
        if len(doi) > 0:
            self.identifiers.append(IndustryIdentifier(doi[0].xpath('text()')[0], "doi", "online"))
        else:
            ids = book.xpath('.//book-id')
            if len(ids) > 0:
                id_text = ids[0].xpath('text()')
                id_type = ids[0].xpath('@book-id-type')
                self.id_other = id_text[0] if len(id_text) > 0 else None
                self.id_type = id_type[0] if len(id_type) > 0 else None
        # Title
        self.title = ' '.join(book.xpath('.//book-title//text()'))
        # Authors or Editors
        contributors = book.xpath('.//book-meta//contrib-group//contrib')
        self.editors = []
        self.authors = []
        for jats_contrib in contributors:
            c = Contributor.from_jats(jats_contrib)
            # This will work for "volume editor", "volume-editor", and other variations
            if "editor" in c.type:
                self.editors.append(c)
            else:
                if c.type == "author":
                    self.authors.append(c)
                else:
                    print("Unknown contributor type", c)
        # Year
        year = book.xpath('.//book-meta/pub-date/year/text()')
        if len(year) > 0:
            # TODO check if the format is correct?
            self.year = year[0]
        # Publisher
        publisher = book.xpath(".//publisher//publisher-name//text()")
        if len(publisher) > 0:
            self.publisher = publisher[0]
        # Location
        loc = book.xpath(".//publisher//publisher-loc//text()")
        if len(loc) > 0:
            self.location = loc[0]
        # ISBN
        isbn_all = book.xpath(".//isbn")
        for isbn in isbn_all:
            pub_format = isbn.xpath('@publication-format')
            pub_id = isbn.xpath("text()")
            if len(pub_id) > 0:
                pub_format = pub_format[0] if len(pub_format) > 0 else ""
                self.identifiers.append(IndustryIdentifier(pub_id[0], "isbn", pub_format))

    def __parse_references(self, jats_root, pub_zip):
        if jats_root is None:
            return
        book_parts = jats_root.xpath('//book-part')
        self.bib_refs = []
        self.index_refs = []
        self.index_files = []
        self.index_types = []
        self._index_skipped = []

        self.index_refs_with_errors = []
        self.bib_refs_with_errors = []

        for book_part in book_parts:
            title = ' '.join(book_part.xpath('.//title//text()')).lower()
            hrefs = book_part.xpath('.//self-uri/@xlink:href', namespaces={"xlink": "http://www.w3.org/1999/xlink"})
            if hrefs and self._extract_bib and 'bibliography' in title or self._extract_index and 'index' in title:
                href = hrefs[0]
                target_pdf = pub_zip.open(href)
                # TODO issue a warning if more than one bibliography file found
                # TODO some JATS files contain bibliography inside and not in PDF (check example in unusual_xml)
                if self._extract_bib and 'bibliography' in title:
                    self.bib_file = href
                    # Extract references and save skipped text from bibliography file for analysis
                    [items, self._bib_skipped] = PdfParser.parse_target_indent(target_pdf)
                    for ref_num, ref_text in enumerate(items):
                        # print(ref_text)
                        try:
                            ref = Reference(text=ref_text, ref_num=ref_num+1, cited_by_doi=self.doi, cited_by_zip=self.zip_path)
                            self.bib_refs.append(ref)
                        except:
                            print("Failed to parse bibliographic reference:", ref_text)
                            self.bib_refs_with_errors.append(ref_text)
                if self._extract_index and 'index' in title:
                    print("Parsing index file", href)
                    self.index_files.append(href)
                    curr_index_types = IndexReference.get_index_types(title)
                    [items, skipped] = PdfParser.parse_target_indent(target_pdf)
                    # Save skipped text from index files for analysis
                    print("\tExtracted index references: ", len(items))
                    print("\tSkipped lines in index file: ", len(skipped))
                    if skipped:
                        self._index_skipped.append(skipped)
                    # Merge lines that start from digid with previous
                    items = [item.replace("\n", " ").strip() for item in items]
                    ref_items = []
                    ref_text = ""
                    for text in items:
                        if text[0].isdigit():
                            ref_text += " " + text
                        else:
                            if ref_text:
                                ref_items.append(ref_text)
                            ref_text = text
                    for ref_num, ref_text in enumerate(ref_items):
                        ref = IndexReference(UUID=str(uuid.uuid4()), text=ref_text, ref_num=ref_num + 1, cited_by_doi=self.doi, cited_by_zip=self.zip_path,
                                             types=curr_index_types)
                        self.index_refs.append(ref)
                        if not ref.refs:
                            # print("Failed to parse index reference:", ref_text)
                            self.index_refs_with_errors.append(ref_text)

    def disambiguate_bib(self):
        if self.bib_refs:
            for ref in self.bib_refs:
                ref.refers_to = []
                DisambiguateBibliographic.find_google_books(ref)
                DisambiguateBibliographic.find_crossref(ref)

    def disambiguate_index(self):
        if self.index_refs:
            for idx in self.index_refs:
                # Many repeated terms
                # TODO optimize via cache dictionary {term: ExternalIndex}?
                # TODO optimize via clustering
                idx.refers_to = []
                for part in idx.refs:
                    if part.label:
                        terms = re.split('[;,.() ]', part.label)
                        for term in terms:
                            if len(term) >= 5:
                                print(term)
                                ext = DisambiguateIndex.find_hucitlib(term)
                                if ext:
                                    print(ext)
                                    idx.refers_to.append(ext)

    def save(self, out_path: str):
        # TODO override to be able to load correctly
        with open(out_path, "w", encoding='utf-8') as out_file:
            data = json.dumps(asdict(self))
            out_file.write(data)

    @classmethod
    def load(cls, in_path: str) -> Publication:
        with open(in_path, "r", encoding='utf-8') as in_file:
            data = in_file.read()
            return cls.from_json(data)

    @property
    def props(self) -> dict:
        props = BasePublication.props.fget(self)
        props["zip_path"] = self.zip_path
        props["jats_file"] = self.jats_file
        props["bib_file"] = self.bib_file
        props["index_files"] = ";".join(self.index_files)
        return props

    @classmethod
    def deserialize(cls, props: dict) -> Publication:
        self = cls(UUID=props["UUID"])
        if "index_files" in props:
            setattr(self, "index_files", props["index_files"].split(";"))
            del props["index_files"]
        for key in props.keys():
            setattr(self, key, props[key])
        return self
