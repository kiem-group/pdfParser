from dataclasses import dataclass
from model.publication import Publication
from pyparsing import (Word, Literal, Group, ZeroOrMore, delimitedList, pyparsing_unicode as ppu,
                       ParseException, Optional)


@dataclass
class IndexReference:
    work: str = None
    start: str = None
    end: str = None


@dataclass
class Index:
    """A class for holding information about a reference"""
    _text: str
    cited_by: Publication = None
    refs: [IndexReference] = None

    def __post_init__(self):
        self.parse()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value):
        self.text = value
        self.parse()

    def parse(self):
        # Reference Pattern 1

        # 1) The text preceding the numbers contains information about work and author being cited
        # 2) The hyphen is used to specify a range of text passages, e.g. lines 124 to 125
        # 3) The semicolon separates a reference from another within the same citation
        # 4) The comma separates the hierarchical levels of the work being cited.
        #   In the example above 1,124-5 stands for from Book 1, Line 124 to Book 1, Line 125
        # 5) When the citation scope is a range, the identical hierarchical level are collapsed:
        #   1.124 - 1.125 can be written as both 1.124-125 or 1.124 s.

        intl_alphas = ppu.Latin1.alphas
        intl_nums = ppu.Latin1.nums
        work = ZeroOrMore(Word(intl_alphas + ".")) + Optional(Literal(',').suppress())
        range_sep = Literal(',') | Literal('.')
        level = Optional(Word(intl_nums) + range_sep.suppress())
        end = Literal('-').suppress() + level + Word(intl_nums) | 's.'
        start = level + Word(intl_nums)
        passages = start("start") + Optional(end("end"))
        index = delimitedList(Group(work("work") + passages("passages")), delim=';')
        try:
            res = index.parseString(self.text)
            self.refs = []
            for ref in res:
                idx_ref = IndexReference(" ".join(ref.work),  ".".join(ref.start), ".".join(ref.end))
                self.refs.append(idx_ref)
        except ParseException:
            print("FAILED TO PARSE", self.text)
