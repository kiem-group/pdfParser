from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json
from lxml import etree
import zipfile
import json
from model.index import Index
from model.reference import Reference
from model.contributor import Contributor
from model.pdf_parser import parse_target_indent, SkippedText
from model.industryIdentifier import IndustryIdentifier
from model.basePublication import BasePublication

@dataclass_json
@dataclass(unsafe_hash=True)
class Publication(BasePublication):
    """A class for holding information about a publication"""

    # Sources
    _zip_path: str = None

    @property
    def zip_path(self) -> str:
        return self._zip_path

    _files: [str] = None

    @property
    def files(self) -> [str]:
        return self._files

    _jats_file: str = None

    @property
    def jats_file(self) -> str:
        return self._jats_file

    text_file: str = None

    # Bibliography and indices
    bib_file: str = None
    index_files: [str] = None
    index_types: [[str]] = None

    bib_refs: [Reference] = None
    index_refs: [Index] = None

    bib_refs_with_errors: [str] = None
    index_refs_with_errors: [str] = None

    _bib_skipped: [SkippedText] = None
    _index_skipped: [[SkippedText]] = None
    _extract_bib: bool = False
    _extract_index: bool = False

    @classmethod
    def from_zip(cls, pub_zip, extract_bib=False, extract_index=False):
        self = cls()
        if pub_zip is not None:
            self._zip_path = pub_zip
            self._extract_bib = extract_bib
            self._extract_index = extract_index
            self._parse_zip()
        return self

    def _parse_zip(self):
        if self.zip_path is None:
            return
        print("Publication archive is being processed:", self.zip_path)
        pub_zip = zipfile.ZipFile(self.zip_path, 'r')
        self._files = pub_zip.namelist()

        for file_name in self.files:
            if file_name.endswith('.xml'):
                # Publication signature will be extracted in the setter
                self._jats_file = file_name
                jats_file = pub_zip.open(file_name)
                jats_root = None
                try:
                    jats_tree = etree.parse(jats_file)
                    jats_root = jats_tree.getroot()
                except:
                    print("Failed to parse JATS file", file_name)
                if jats_root is not None:
                    self.parse_book(jats_root)
                    self.parse_index(jats_root, pub_zip)
                jats_file.close()
        pub_zip.close()

    def parse_index(self, jats_root, pub_zip):
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
                    [items, self._bib_skipped] = parse_target_indent(target_pdf)
                    for ref_num, ref_text in enumerate(items, start=0):
                        # print(ref_text)
                        try:
                            ref = Reference(ref_text, ref_num=ref_num+1, cited_by_doi=self.doi, cited_by_zip=self.zip_path)
                            self.bib_refs.append(ref)
                        except:
                            print("Failed to parse bibliographic reference:", ref_text)
                            self.bib_refs_with_errors.append(ref_text)
                if self._extract_index and 'index' in title:
                    print("Parsing index file", href)
                    self.index_files.append(href)
                    curr_index_types = Index.get_index_types(title)
                    self.index_types.append(curr_index_types)
                    [items, skipped] = parse_target_indent(target_pdf)
                    # Save skipped text from index files for analysis
                    print("\tExtracted index references: ", len(items))
                    print("\tSkipped lines: ", len(skipped))
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
                    for ref_num, ref_text in enumerate(ref_items, start=0):
                        ref = Index(ref_text, ref_num=ref_num+1, cited_by_doi=self.doi, cited_by_zip=self.zip_path,
                                    types=curr_index_types)
                        self.index_refs.append(ref)
                        if not ref.refs:
                            # print("Failed to parse index reference:", ref_text)
                            self.index_refs_with_errors.append(ref_text)

    def parse_book(self, jats_root):
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
            if c.type == "editor":
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

    def save(self, out_path):
        with open(out_path, "w", encoding='utf-8') as out_file:
            data = json.dumps(asdict(self))
            out_file.write(data)

    @classmethod
    def load(cls, in_path):
        with open(in_path, "r", encoding='utf-8') as in_file:
            data = in_file.read()
            return cls.from_json(data)
