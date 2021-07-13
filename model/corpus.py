from dataclasses import dataclass
from model.publication import Publication


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

