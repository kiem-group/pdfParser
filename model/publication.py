from dataclasses import dataclass


@dataclass
class Publication:
    """A class for holding information about a publication"""

    zip_path: str
    dir_name: str
    files: [str]
    jats_file: str=None
    text_file: str=None
    bib_file: str=None
    index_files: [str]=None
    index_types: [[str]]=None
    title: str=None
    authors: [str]=None

    corpus_dir_path: str = None



