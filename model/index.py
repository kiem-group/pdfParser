from dataclasses import dataclass
from pyparsing import (Word, Literal, Group, ZeroOrMore, OneOrMore, restOfLine, delimitedList, pyparsing_unicode as ppu,
                       ParseException, Optional)
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class IndexReference:
    work: str = None
    passages: [str] = None
    nested: str = None
    # Filled for index locorum
    start: str = None
    end: str = None


@dataclass_json
@dataclass
class Index:
    """A class for holding information about a reference"""
    _text: str
    cited_by_doi: str = None
    cited_by_zip: str = None
    ref_num: int = 0
    refs: [IndexReference] = None
    types: [str] = None

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
        self._text = self._text.replace("\n", " ")
        print("Parsing index text:", self._text)
        if len(self.text) < 5:
            print("Index text is too short", self.text)
            return
        if len(self.text) > 300:
            print("Index text is too long", self.text)
            return
        if self.types:
            self.refs = []
            if "verborum" in self.types:
                print("  as verborum")
                self.parse_as_verborum()
            else:
                if "locorum" in self.types:
                    print("  as locorum")
                    self.parse_as_locorum()
                else:
                    if "nominum_ancient" in self.types:
                        print("  as nominum ancient")
                        self.parse_as_nominum_ancient()
                    else:
                        if "nominum_modern" in self.types:
                            print("  as nominum modern")
                            self.parse_as_nominum_modern()
                        else:
                            if "rerum" in self.types:
                                print("  as rerum")
                                self.parse_as_rerum()
                            else:
                                print("No parsers for this index type yet", ", ".join(self.types), self.text)
        else:
            print("Unclassified index:", self.text)

    def parse_as_locorum(self):
        try:
            return self.parse_pattern1()
        except ParseException:
            print("Failed to parse index locorum: ", self.text)

    def parse_as_verborum(self):
        print("No parser for index verborum", self.text)

    def parse_as_nominum_ancient(self):
        print("No parser for index nominum (ancient)", self.text)

    def parse_as_nominum_modern(self):
        print("No parser for index nominum (modern)", self.text)

    def parse_as_rerum(self):
        try:
            self.parse_pattern2()
        except ParseException:
            print("Failed to parse index rerum: ", self.text)

    def parse_pattern2(self):
        # Adonis (Plato Comicus), 160, 161, 207
        intl_alphas = ppu.Latin1.alphas
        intl_nums = ppu.Latin1.nums
        work_details = Optional(Literal('(') + OneOrMore(Word(intl_alphas)).setParseAction(' '.join) + Literal(')')).setParseAction(''.join)
        work = OneOrMore(Word(intl_alphas)).setParseAction(' '.join) + work_details
        # work.setName("work").setDebug()
        passages = OneOrMore(Word(intl_nums + 'n' + '–') + Optional(",").suppress())
        index = work("work") + Optional(Literal(',').suppress()) + passages("passages") + restOfLine('rest')
        ref = index.parseString(self.text)
        idx_ref = IndexReference(work=" ".join(ref.work), passages=ref.passages, nested=ref.rest)
        self.refs.append(idx_ref)
        print(idx_ref)

    def parse_pattern1(self):
        # "Hom. Il. 1,124-125"
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
        res = index.parseString(self.text)
        for ref in res:
            idx_ref = IndexReference(work=" ".join(ref.work), start=".".join(ref.start), end=".".join(ref.end))
            self.refs.append(idx_ref)
            print(idx_ref)

    @classmethod
    def get_index_types(cls, index_title):
        keywords = {
            'verborum': ['general', 'verborum', 'verborvm', 'abstract', 'word', 'words', 'term', 'terms', 'termes',
                         'wort', 'sachindex', 'général', 'generalis', 'mots'],
            'locorum': ['locorum', 'loco', 'rum', 'locorvm', 'biblical', 'non-biblical', 'quran', 'biblicum',
                        'citation', 'citations', 'quotation', 'quotations', 'source', 'sources', 'reference',
                        'references',
                        'scripture', 'scriptures', 'verse', 'verses', 'passage', 'passages', 'line', 'lines', 'cited',
                        'textes', 'cités', 'papyri', 'fragmentorum'],
            'nominum_ancient': ['nominum', 'nominvm', 'propriorvm', 'name', 'names',
                                'proper', 'person', 'persons', 'personal', 'people', 'writer', 'writers', 'poet',
                                'poets',
                                'author', 'authors',
                                'ancient', 'antique', 'classical', "medieval", 'greek', 'egyptian', 'latin',
                                'auteur', 'auteurs', 'anciens',
                                'eigennamen', 'noms', 'propres', 'personnages'],
            'nominum_modern': ['modern', 'author', 'authors', 'editor', 'editors', 'scholar', 'scholars', 'auteur',
                               'auteurs', 'modernes'],
            'rerum': ['rerum', 'rervm', 'subject', 'subjects', 'theme', 'themes', 'topic', 'topics', 'thématique',
                      'thematic'],
            'geographicus': ['geographicus', 'geographic', 'geographical', 'géographique', 'place', 'places',
                             'location', 'locations', 'site', 'sites', 'topographical'],
            'bibliographicus': ['bibliographicus', 'bibliographique', 'bibliographical', 'bibliographic', 'manuscript',
                                'manuscripts', 'collections', 'ventes'],
            'museum': ['museum', 'museums', 'meseums', 'musées', 'collections'],
            'epigraphic': ['epigraphic', 'epigraphical', 'inscriptionum', 'inscriptions']
        }
        # exclude_keywords ?

        index_terms = [term for term in index_title.split(" ") if len(term.strip()) > 3]
        if len(index_terms) == 1:
            return ['verborum']
        hits = {}
        max_hit = 0
        for term in index_terms:
            for key in keywords.keys():
                for keyword in keywords[key]:
                    if keyword == term:
                        hits[key] = hits.get(key, 0) + 1
                        if hits[key] > max_hit:
                            max_hit = hits[key]
        if not bool(hits.keys()):
            print(index_title)
            return ['unknown']
        # return hits.keys()
        return [k for k, v in hits.items() if v == max_hit]

        # index of very specific stuff
        # 'index of scribal errors'
        # 'index of verse-end corruptions'
        # 'index of verse-end borrowings'
        # 'index of grammatical topics'
        # 'index of greek words'

    # Guess type of index. Can return several types
    # verborum - index of words
    # locorum  - index of references
    # nominum  - index of names
    # nominum_ancient - ancient people
    # nominum_modern  - modern authors
    # rerum    - index of subjects
    # geographicus - index of places