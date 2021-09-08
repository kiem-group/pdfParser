from dataclasses import dataclass
from dataclasses_json import dataclass_json
from lxml import etree
import zipfile

from model.index import Index
from model.reference import Reference
from model.contributor import Contributor
from model.pdf_parser import parse_target_indent, SkippedText


@dataclass_json
@dataclass
class Publication:
    """A class for holding information about a publication"""

    def __post_init__(self):
        self.parse_zip()

    # Sources
    _zip_path: str

    @property
    def zip_path(self) -> str:
        return self._zip_path

    @zip_path.setter
    def zip_path(self, value):
        self._zip_path = value
        self.parse_zip()

    # Signature
    doi: str = None
    id_other: str = None
    id_type: str = None
    title: str = None
    authors: [Contributor] = None
    editors: [Contributor] = None
    year: str = None
    lang: str = None
    publisher: str = None
    location: str = None

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

    extract_bib: bool = False
    extract_index: bool = False
    bib_refs: [Reference] = None
    index_refs: [Index] = None

    _bib_skipped: [SkippedText] = None
    _index_skipped: [[SkippedText]] = None

    def parse_zip(self):
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
        # Old function that saves parsed text from pdf
        def save_to_file(items, out_path):
            with open(out_path, "w", encoding='utf-8') as out_file:
                for item in items:
                    out_file.write(item.to_dict())
                out_file.write("\n")

        if jats_root is None:
            return
        book_parts = jats_root.xpath('//book-part')
        self.bib_refs = []
        self.index_refs = []
        self.index_files = []
        self.index_types = []
        self._index_skipped = []
        for book_part in book_parts:
            title = ' '.join(book_part.xpath('.//title//text()')).lower()
            hrefs = book_part.xpath('.//self-uri/@xlink:href', namespaces={"xlink": "http://www.w3.org/1999/xlink"})
            if hrefs and self.extract_bib and 'bibliography' in title or self.extract_index and 'index' in title:
                href = hrefs[0]
                target_pdf = pub_zip.open(href)
                # TODO issue a warning if more than one bibliography file found
                # TODO some JATS files contain bibliography inside and not in PDF (check example in unusual_xml)
                if self.extract_bib and 'bibliography' in title:
                    self.bib_file = href
                    # Extract references and save skipped text from bibliography file for analysis
                    [items, self._bib_skipped] = parse_target_indent(target_pdf)
                    for ref_num, ref_text in enumerate(items, start=0):
                        try:
                            ref = Reference(ref_text, ref_num=ref_num+1, cited_by_doi=self.doi, cited_by_zip=self.zip_path)
                            self.bib_refs.append(ref)
                        except:
                            print("Failed to parse bibliographic reference:", ref_text)
                if self.extract_index and 'index' in title:
                    print("Parsing index file", href)
                    self.index_files.append(href)
                    curr_index_types = Index.get_index_types(title)
                    self.index_types.append(curr_index_types)
                    [items, skipped] = parse_target_indent(target_pdf)
                    # Save skipped text from index files for analysis
                    print("Parsed index file: ", len(items), len(skipped))
                    if skipped:
                        self._index_skipped.append(skipped)
                    # Merge lines that start from digid with previous
                    items = [item.replace("\n", " ").strip() for item in items]
                    ref_items = []
                    ref_text = ""
                    print("Extracted indices: ", len(items))
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
                    # Save for analysis
                    # ext = "-" + str(len(self.index_files)) + "_" + ('-'.join(curr_index_types))
                    # out_path = self.zip_path + ext + ".json"
                    # print("Saving indices in: ", out_path)
                    # TODO fix
                    # save_to_file(self.index_refs, out_path)

    def parse_book(self, jats_root):
        if jats_root is None:
            return
        book = jats_root.xpath('//book')[0]
        lang = book.xpath('//@xml:lang', namespaces={"xml": "https://www.w3.org/XML/1998/namespace"})
        self.lang = lang[0] if len(lang) > 0 else None
        doi = book.xpath('.//book-meta/book-id[@book-id-type="doi"]')
        if len(doi) > 0:
            self.doi = doi[0].xpath('text()')[0]
        else:
            ids = book.xpath('.//book-id')
            if len(ids) > 0:
                id_text = ids[0].xpath('text()')
                id_type = ids[0].xpath('@book-id-type')
                self.id_other = id_text[0] if len(id_text) > 0 else None
                self.id_type = id_type[0] if len(id_type) > 0 else None
                print(self.id_other, self.id_type)
        self.title = ' '.join(book.xpath('.//book-title//text()'))
        contributors = book.xpath('.//book-meta//contrib-group//contrib')
        self.editors = []
        self.authors = []
        for jats_contrib in contributors:
            c = Contributor(jats_contrib)
            if c.type == "editor":
                self.editors.append(c)
            else:
                if c.type == "author":
                    self.authors.append(c)
                else:
                    print("Unknown contributor type", c)
        year = book.xpath('.//book-meta/pub-date/year/text()')
        if len(year) > 0:
            # TODO check if the format is correct?
            self.year = year[0]
        publisher = book.xpath(".//publisher//publisher-name//text()")
        if len(publisher) > 0:
            self.publisher = publisher[0]
        loc = book.xpath(".//publisher//publisher-loc//text()")
        if len(loc) > 0:
            self.location = loc[0]
        # TODO extract isbn if needed
        # < isbn publication-format = "print" > 9783506782113 < / isbn >
        # < isbn publication-format = "online" > 9783657782116 < / isbn >