from dataclasses import dataclass


@dataclass
class Publication:
    """A class for holding information about a publication"""

    zip_path: str
    files: [str]
    jats_file: str=None
    text_file: str=None
    ref_file: str=None
    index_files: [str]=None
    title: str=None
    authors: [str]=None
