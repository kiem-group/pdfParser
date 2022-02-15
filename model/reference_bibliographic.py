from __future__ import annotations
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import re
from pyparsing import (Word, Char, Literal, OneOrMore, delimitedList, restOfLine, pyparsing_unicode as ppu,
                       ParseException, Optional, Regex, CaselessKeyword, Combine, CharsNotIn)
from model.publication_external import ExternalPublication
from model.reference_base import BaseReference


@dataclass_json
@dataclass
class Reference(BaseReference):
    """A class for holding information about a bibliographic reference"""
    author: str = None
    title: str = None
    year: str = None
    refers_to: [ExternalPublication] = None
    follows: Reference = None

    def parse(self):
        if not self.text:
            return
        self.text = self.text.replace("\n", " ").replace('"', '”')
        dot = Literal('.')
        comma = Literal(',')
        intl_alphas = ppu.Latin1.alphas + ppu.LatinA.alphas + ppu.LatinB.alphas
        family_name = Word(intl_alphas+'-', min=2)
        init_name = Char(intl_alphas) + dot + Optional('-' + Char(intl_alphas) + dot)
        # family_name.setName('LastName').setDebug()
        same = Word('—') + dot.suppress()
        eds = CaselessKeyword("ed") | CaselessKeyword("eds")
        year_or_range = r"\d{4}[a-z]?([,–,-]\d{4})?"
        year = Regex(year_or_range) + Optional(dot).suppress() + Optional(comma).suppress()
        author = family_name("LastName") + comma + OneOrMore(init_name("FirstName"))
        author_list = Combine((author | same) + Optional(eds).suppress() + Optional(dot).suppress() + Optional(comma).suppress())
        citation = author_list('author') + year('year') + restOfLine('title')
        year_anywhere = None
        try:
            year_anywhere = re.search(year_or_range, self.text).group(0)
        except AttributeError:
            pass
        try:
            res = citation.parseString(self.text)
            self.author = res.author
            if res.year:
                self.year = res.year[0]
            self.title = res.title
            part = re.search(r'“(.*?)”', self.title)
            if part:
                self.title = part.group(1)
            else:
                parts = self.title.split('.')
                self.title = parts[0]
        except ParseException:
            if len(self.text) > 10:
                text_to_parse = self.text.replace(year_anywhere, "") if year_anywhere is not None else self.text
                # If found, use the text in quotes as title
                part = re.search(r'“(.*?)”', text_to_parse)
                if part:
                    self.title = part.group(1).replace(".", "")
                else:
                    # If not found, use the longest part as title
                    parts = re.split('[;,.()]', text_to_parse)
                    self.title = max(parts, key=len)
                # Use anything before title as author string
                text_to_parse = text_to_parse.replace("“", "")
                self.author = text_to_parse.partition(self.title)[0].strip()
        if self.year is None and year_anywhere:
            self.year = year_anywhere
        self.title = self.title.strip()

    @property
    def derived_author(self) -> str:
        if self.follows is not None:
            return self.follows.author
        else:
            return self.author

    @property
    def derived_text(self) -> str:
        return self.text.replace(self.author, self.derived_author).replace("..", ".").replace(" .", "")

    @property
    def props(self) -> dict:
        props = BaseReference.props.fget(self)
        props["author"] = self.author
        props["title"] = self.title
        props["year"] = self.year
        props["derived_author"] = self.derived_author
        return props

    @classmethod
    def deserialize(cls, props: dict) -> Reference:
        self = cls(UUID=props["UUID"])
        if "derived_author" in props:
            del props["derived_author"]
        if "author" in props:
            setattr(self, "author", props["author"])
            del props["author"]
        for key in props.keys():
            setattr(self, key, props[key])
        return self
