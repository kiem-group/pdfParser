from dataclasses import dataclass
from dataclasses_json import dataclass_json
import re
from pyparsing import (Word, Literal, ZeroOrMore, delimitedList, restOfLine, pyparsing_unicode as ppu,
                       ParseException, Optional, Regex, CaselessKeyword)
from model.publication_external import ExternalPublication
from model.reference_base import BaseReference


@dataclass_json
@dataclass
class ReferencePart(BaseReference):
    """A class for holding information about a bibliographic reference"""
    authors: [str] = None
    title: str = None
    year: str = None
    refers_to: [ExternalPublication] = None

    def parse(self):
        if not self.text:
            return
        self.text = self.text.replace("\n", " ")
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
                text_to_parse = self.text.replace(year_anywhere, "") if year_anywhere is not None else self.text
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
        props = BaseReference.props.fget(self)
        props["authors"] = ";".join(self.authors)
        props["title"] = self.title
        props["year"] = self.year
        return props


@dataclass
class Reference(ReferencePart):
    """A class for holding information about reference with authors like in a given reference"""

    follows: ReferencePart = None
