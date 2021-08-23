from dataclasses import dataclass
from dataclasses_json import dataclass_json
from model.publication import Publication
import re
from pyparsing import (Word, Literal, ZeroOrMore, delimitedList, restOfLine, pyparsing_unicode as ppu, ParseException, Optional, Regex)


@dataclass_json
@dataclass
class BaseReference:
    """A class for holding information about a reference"""

    _text: str
    cited_by: Publication = None
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
        year = Regex('.{' + str(4) + '}') + Literal('.').suppress()
        citation = author_list('authors') + Optional(year('year')) + restOfLine('rest')
        try:
            res = citation.parseString(self.text)
            self.authors = res.authors.asList()
            self.year = res.year
            self.title = res.rest
            parts = res.rest.split('.')
            self.title = parts[0].replace("“", "")
        except ParseException:
            # print("FAILED TO PARSE", self.text)
            # Trivial - find year
            try:
                self.year = re.search(r"(\d{4})", self.text).group(1)
            except AttributeError:
                del self.year
            parts = re.split('[;,.()]', self.text)
            self.title = max(parts, key=len)
            self.authors = self.text.partition(self.title)[0]


@dataclass
class Reference(BaseReference):
    """A class for holding information about reference with authors like in given reference"""

    follows: BaseReference = None
