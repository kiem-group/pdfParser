from dataclasses import dataclass
from pyparsing import (Word, Literal, Group, ZeroOrMore, OneOrMore, oneOf, restOfLine, delimitedList, pyparsing_unicode as ppu,
                       ParseException, Optional)
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class IndexReference:
    label: str = None
    locus: str = None
    occurrences: [str] = None
    note: str = None
    # TODO add possibility to indicate occurrences in bold or footnotes

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

    # An argument to distinguish between parsing of index references in text vs index files
    inline: bool = False

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
        if len(self.text) > 3000:
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
            if self.inline:
                return self.parse_pattern1_inline()
            else:
                return self.parse_locorum_pattern1()
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
            self.parse_rerum_pattern1()
        except ParseException:
            print("Failed to parse index rerum: ", self.text)

    # @Examples:
    #   Adespota elegiaca (IEG)  23 206
    #   Aeschines 2.157 291
    def parse_locorum_pattern1(self):
        intl_alphas = ppu.Latin1.alphas
        intl_nums = ppu.Latin1.nums
        occurrences = delimitedList(Word(intl_nums), delim=",")
        locus_fragment = Word(intl_nums+".–=") + Optional(oneOf("ff."))
        locus = locus_fragment + Optional('/'+locus_fragment)
        label_details = Optional(Literal('(') + OneOrMore(Word(intl_alphas+','+'.')).setParseAction(' '.join) + Literal(')')).setParseAction(''.join)
        label = OneOrMore(Word(intl_alphas+','+'.')) + label_details
        # label.setName("label").setDebug()
        index = Optional(label("label")) + Optional(locus("locus").setParseAction(''.join) + occurrences('occurrences') + restOfLine("rest"))
        text = self.text
        the_end = False
        while not the_end:
            ref = index.parseString(text)
            idx_ref = IndexReference(label=" ".join(ref.label).strip(), locus=ref.locus,
                occurrences=ref.occurrences)
            self.refs.append(idx_ref)
            text = ref.rest
            the_end = True if len(text) == 0 else False
            if the_end:
               idx_ref.note = text

    # @Example: Adonis (Plato Comicus), 160, 161, 207
    def parse_rerum_pattern1(self):
        intl_alphas = ppu.Latin1.alphas
        intl_nums = ppu.Latin1.nums
        label_details = Optional(Literal('(') + OneOrMore(Word(intl_alphas)).setParseAction(' '.join) + Literal(')')).setParseAction(''.join)
        label = OneOrMore(Word(intl_alphas)).setParseAction(' '.join) + label_details
        # label.setName("label").setDebug()
        occurrences = OneOrMore(Word(intl_nums + 'n' + '–') + Optional(",").suppress())
        index = label("label") + Optional(Literal(',').suppress()) + occurrences("occurrences") + restOfLine('rest')
        ref = index.parseString(self.text)
        idx_ref = IndexReference(label=" ".join(ref.label), occurrences=ref.occurrences, note=ref.rest)
        self.refs.append(idx_ref)
        print(idx_ref)

    # Inline pattern, only needed for testing
    def parse_pattern1_inline(self):
        # This is a patten for the inline style of indices, e.g., "Hom. Il. 1,124-125"
        # 1) The text preceding the numbers contains information about work and author being cited
        # 2) The hyphen is used to specify a range of text passages, e.g. lines 124 to 125
        # 3) The semicolon separates a reference from another within the same citation
        # 4) The comma separates the hierarchical levels of the work being cited.
        #   In the example above 1,124-5 stands for from Book 1, Line 124 to Book 1, Line 125
        # 5) When the citation scope is a range, the identical hierarchical level are collapsed:
        #   1.124 - 1.125 can be written as both 1.124-125 or 1.124 s.
        intl_alphas = ppu.Latin1.alphas
        intl_nums = ppu.Latin1.nums
        label = ZeroOrMore(Word(intl_alphas + ".")) + Optional(Literal(',').suppress())
        range_sep = Literal(',') | Literal('.')
        level = Optional(Word(intl_nums) + range_sep.suppress())
        end = Literal('-').suppress() + level + Word(intl_nums) | 's.'
        start = level + Word(intl_nums)
        locus = start("start") + Optional(end("end"))
        index = delimitedList(Group(label("label") + locus("locus")), delim=';')
        res = index.parseString(self.text)
        for ref in res:
            locus_txt = ref.locus[0]+ "." + ref.locus[1]
            if len(ref.locus) > 2:
                locus_txt += "-" + ref.locus[2]
            idx_ref = IndexReference(label=" ".join(ref.label), locus=locus_txt)
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