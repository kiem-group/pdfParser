from dataclasses import dataclass
from dataclasses_json import dataclass_json
from lxml import etree
from contributor import Contributor
import zipfile


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
                self.parse_jats(jats_file)
                jats_file.close()
            # TODO place here bibliography and index parsing
        pub_zip.close()

    def parse_jats(self, jats_file):
        if jats_file is None:
            return
        jats_tree = etree.parse(jats_file)
        jats_root = jats_tree.getroot()
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
        # TODO extract isbn is needed
        # < isbn publication-format = "print" > 9783506782113 < / isbn >
        # < isbn publication-format = "online" > 9783657782116 < / isbn >