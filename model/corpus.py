from dataclasses import dataclass
from model.publication import Publication
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Corpus:
    """A class for holding information about a corpus of publications"""

    zip_path: str
    publications: [Publication]

    index_count: int = 0
    bibliography_count: int = 0

    xml_parsing_errors: int = 0
    format_errors: int = 0
    other_errors: int = 0

    def add_publication(self, pub):
        if pub is None:
            return
        self.publications.append(pub)
        self.index_count += len(pub.index_files) if pub.index_files else 0
        if pub.bib_file:
            self.bibliography_count += 1
        else:
            self.xml_parsing_errors += 1

