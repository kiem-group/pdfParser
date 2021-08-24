from dataclasses import dataclass


@dataclass
class ParserConfig:
    """A class that defines parameters for indentation-based PDF parser"""

    indent: int = 150      # Maximal horizontal offset to consider the next line a continuation of the previous
    noise: int = 3         # Minimal threshold on lines with certain indentation. Helps to exclude non-references
    min_length: int = 30   # Minimal length of the reference or index term, to exclude page numbers, titles, etc.
    max_length: int = 300  # Maximal length of the reference or index term, to exclude article content
    min_words: int = 3     # Minimal number of words in reference or index (currently not used)
    max_words: int = 100   # Maximal number of words in reference or index (currently not used)
