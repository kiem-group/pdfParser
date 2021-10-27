from dataclasses import dataclass
from dataclasses_json import dataclass_json
import re
from pyparsing import (Word, Literal, ZeroOrMore, delimitedList, restOfLine, pyparsing_unicode as ppu,
                       ParseException, Optional, Regex, CaselessKeyword)
from model.externalPublication import ExternalPublication

@dataclass_json
@dataclass
class BaseReference:
    """A class for holding information about a reference"""

    _text: str
    cited_by_doi: str = None
    cited_by_zip: str = None
    ref_num: int = 0
    authors: [str] = None
    title: str = None
    year: str = None

    refers_to: [ExternalPublication] = None

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
        author_list = delimitedList(author) | same + \
            Optional(CaselessKeyword("ed").suppress()) + Optional(Literal('.').suppress())
        year_or_range = r"\d{4}[a-z]?([,–,-]\d{4})?"
        year = Regex(year_or_range) + Literal('.').suppress()
        citation = author_list('authors') + year('year') + restOfLine('rest')
        year_anywhere = None
        try:
            year_anywhere = re.search(year_or_range, self.text).group(0)
        except AttributeError:
            pass
        try:
            res = citation.parseString(self.text)
            self.authors = res.authors.asList()
            if res.year:
                self.year = res.year[0]
            parts = res.rest.split('.')
            self.title = parts[0]
        except ParseException:
            if len(self.text) > 10:
                text_to_parse = self._text.replace(year_anywhere, "") if year_anywhere is not None else self._text
                parts = re.split('[;,.()]', text_to_parse)
                # Use the longest part as title
                self.title = max(parts, key=len)
                # Use anything before title as authors string
                self.authors = text_to_parse.partition(self.title)[0]
        if self.year is None and year_anywhere:
            self.year = year_anywhere
        self.title = self.title.replace("“", "").strip()

    @property
    def props(self) -> dict:
        return {
            "text": self._text,
            "authors": ", ".join(self.authors),
            "title": self.title,
            "year": self.year,
            "ref_num": self.ref_num
            # "cited_by_doi": self.sited_by_doi,
            # "cited_by_zip": self.sited_by_zip
        }

    def serialize(self):
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"


@dataclass
class Reference(BaseReference):
    """A class for holding information about reference with authors like in given reference"""

    follows: BaseReference = None
