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
import logging

module_logger = logging.getLogger('pdfParser.publication')


@dataclass_json
@dataclass(unsafe_hash=True)
class Publication(BasePublication):
    """A class for holding information about a publication"""

    # Sources
    zip_path: str = None
    jats_file: str = None
    bib_file: str = None
    index_files: [str] = None

    # stats
    is_collection: bool = None
    page_count: int = None

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
        module_logger.info('Extracting publication from zip: ' + pub_zip)
        self = cls()
        if pub_zip is not None:
            self.zip_path = pub_zip
            self._extract_bib = extract_bib
            self._extract_index = extract_index
            self.__parse_zip()
        return self

    def __parse_zip(self):
        self.logger.info("Parsing publication from zip: " + self.zip_path)
        if self.zip_path is None:
            return
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
                    self.logger.error("Failed to parse JATS file: " + file_name)
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
            pub_format = issn[0].xpath('@publication-format')
            pub_id = issn[0].xpath("text()")
            if len(pub_id) > 0:
                pub_format = pub_format[0] if len(pub_format) > 0 else None
                self.identifiers.append(IndustryIdentifier(pub_id[0], "issn", pub_format))

        collection_meta = book.xpath('.//collection-meta')
        self.is_collection = True if len(collection_meta) > 0 else False
        page_counts = book.xpath('.//counts/book-page-count')
        if len(page_counts) > 0:
            counts = page_counts[0].xpath('@count')
            self.page_count = int(counts[0]) if len(counts) > 0 else None

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
        # TODO How to handle chapter authors???
        contributors = book.xpath('.//book-meta//contrib-group//contrib')
        self.editors = []
        self.authors = []
        for jats_contrib in contributors:
            c = Contributor.from_jats(jats_contrib)
            # This will work for "volume editor", "volume-editor", and other variations
            if "editor" in c.type.lower():
                self.editors.append(c)
            else:
                if "author" in c.type.lower():
                    self.authors.append(c)
                else:
                    self.logger.warning("Unknown contributor type: %s", c.type)
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
                pub_format = pub_format[0] if len(pub_format) > 0 else None
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

        # Extract (structured) back matter from JATS
        jats_bibs = jats_root.xpath('//ref-list')
        if len(jats_bibs) > 0:
            self.__extract_jats_refs(jats_bibs[0])
        jats_idx_groups = jats_root.xpath('//index')
        for jats_idx in jats_idx_groups:
            self.__extract_jats_idx(jats_idx)

        # Extract back matter from PDF
        for book_part in book_parts:
            titles = book_part.xpath('.//title/text()')
            if len(titles) < 1:
                continue
            title = book_part.xpath('.//title/text()')[0].lower()
            hrefs = book_part.xpath('.//self-uri/@xlink:href', namespaces={"xlink": "http://www.w3.org/1999/xlink"})
            if len(hrefs) < 1:
                continue
            self.__extract_pdf_refs(title, hrefs[0], pub_zip)
            self.__extract_pdf_idx(title, hrefs[0], pub_zip)

    def __extract_pdf_refs(self, title, href, pub_zip):
        if 'bibliography' in title:
            self.bib_file = href
            if self._extract_bib:
                target_pdf = pub_zip.open(href)
                [items, self._bib_skipped] = PdfParser.parse_target_indent(target_pdf)
                for idx, ref_text in enumerate(items):
                    self.__create_ref(ref_text, idx)

    def __extract_pdf_idx(self, title, href, pub_zip):
        if 'index' in title:
            self.index_files.append(href)
            if self._extract_index:
                target_pdf = pub_zip.open(href)
                curr_index_types = IndexReference.get_index_types(title)
                [items, skipped] = PdfParser.parse_target_indent(target_pdf)
                # Save skipped text from index files for analysis
                self.logger.info("Extracted index references: " + str(len(items)))
                self.logger.info("Skipped lines in index file: " + str(len(skipped)))
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
                for idx, ref_text in enumerate(ref_items):
                    self.__create_index_ref(ref_text, idx, curr_index_types)

    def __extract_jats_refs(self, jats_bib):
        if self._extract_bib:
            refs = jats_bib.xpath('.//ref')
            for idx, ref in enumerate(refs):
                ref_text = ''.join(ref.xpath('.//text()'))
                self.__create_ref(ref_text, idx)

    def __extract_jats_idx(self, jats_idx):
        if self._extract_index:
            titles = jats_idx.xpath('.//index-title-group//title/text()')
            curr_index_types = ["unknown"]
            if len(titles) > 0:
                title = titles[0].lower()
                curr_index_types = IndexReference.get_index_types(title)
            ref_items = jats_idx.xpath('.//index-entry')
            for idx, idx_item in enumerate(ref_items):
                ref_text = ''.join(idx_item.xpath('.//text()'))
                self.__create_index_ref(ref_text, idx, curr_index_types)

    def __create_ref(self, ref_text, idx):
        try:
            ref = Reference(text=ref_text, ref_num=idx + 1, cited_by_doi=self.doi, cited_by_zip=self.zip_path)
            if ref_text.startswith('——') and idx > 0:
                ref.follows = self.bib_refs[idx - 1]
            self.bib_refs.append(ref)
        except Exception as e:
            self.logger.warning("Failed to parse bibliographic reference: " + ref_text)
            self.logger.error(e)
            self.bib_refs_with_errors.append(ref_text)

    def __create_index_ref(self, ref_text, idx, curr_index_types):
        ref = IndexReference(text=ref_text, ref_num=idx + 1, cited_by_doi=self.doi, cited_by_zip=self.zip_path,
                             types=curr_index_types)
        self.index_refs.append(ref)
        if not ref.refs:
            self.logger.warning("Failed to parse index reference: " + ref_text)
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
                DisambiguateIndex.find_wikidata(idx)

    @property
    def num_disambiguated_refs(self) -> int:
        count = 0
        if self.bib_refs:
            for ref in self.bib_refs:
                count += 1 if len(ref.refers_to or []) > 0 else 0
        return count

    @property
    def props(self) -> dict:
        props = BasePublication.props.fget(self)
        props["zip_path"] = self.zip_path
        props["jats_file"] = self.jats_file
        props["bib_file"] = self.bib_file
        if self.index_files:
            props["index_files"] = ";".join(self.index_files)
        return props

    @classmethod
    def deserialize(cls, props: dict) -> Publication:
        module_logger.info('Deserializing publication: ' + props["UUID"])
        self = cls(UUID=props["UUID"])
        if "index_files" in props:
            setattr(self, "index_files", props["index_files"].split(";"))
            del props["index_files"]
        for key in props.keys():
            setattr(self, key, props[key])
        return self
