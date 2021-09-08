from dataclasses import dataclass
from dataclasses_json import dataclass_json
import re
from pyparsing import (Word, Literal, ZeroOrMore, delimitedList, restOfLine, pyparsing_unicode as ppu, ParseException, Optional, Regex)


@dataclass_json
@dataclass
class BaseReference:
    """A class for holding information about a reference"""

    _text: str
    cited_by_doi: str = None
    cited_by_zip: str = None
    ref_num: int = 0
    authors: str = None
    title: str = None
    year: str = None

    def __post_init__(self):
        self.parse()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.parse()

    def parse(self):
        self._text = self._text.replace("\n", " ")

        # Reference Pattern 1

        intl_alphas = ppu.Latin1.alphas
        family_name = Word(intl_alphas + '-')
        first_init = Word(intl_alphas + '-' + '.')
        author = family_name("LastName") + Literal(',').suppress() + ZeroOrMore(first_init("FirstName"))
        # author.setName("author").setDebug()
        same = Word('—') + Literal('.').suppress()
        author_list = delimitedList(author) | same
        year_or_range = r"[\S]{4}[a-z]?([,–][\S]{4})?"
        year = Regex(year_or_range) + Literal('.').suppress()
        citation = author_list('authors') + Optional(year('year')) + restOfLine('rest')
        try:
            res = citation.parseString(self.text)
            self.authors = res.authors.asList()
            if res.year:
                self.year = res.year[0]
            parts = res.rest.split('.')
            self.title = parts[0].replace("“", "")
        except ParseException:
            # print("FAILED TO PARSE", self.text)
            # Trivial - find year
            try:
                self.year = re.search(year_or_range, self.text).group(1)
            except AttributeError:
                del self.year
            parts = re.split('[;,.()]', self.text)
            # Use longest part as title
            self.title = max(parts, key=len)
            # Use anything before title as authors string
            self.authors = self.text.partition(self.title)[0]
        self.title = self.title.strip()

@dataclass
class Reference(BaseReference):
    """A class for holding information about reference with authors like in given reference"""

    follows: BaseReference = None
