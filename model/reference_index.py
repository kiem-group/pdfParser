from dataclasses import dataclass
from pyparsing import (Word, Literal, Group, ZeroOrMore, OneOrMore, oneOf, restOfLine, delimitedList, pyparsing_unicode as ppu,
                       ParseException, Optional, CaselessKeyword)
from dataclasses_json import dataclass_json
from model.reference_base import BaseReference
import uuid


@dataclass_json
@dataclass
class IndexReferencePart:
    """A class for holding information about a single reference part in a composite index"""
    label: str = None
    locus: str = None
    occurrences: [str] = None
    note: str = None
    is_bold: bool = False
    is_footnote: bool = False
    UUID: str = None

    def __post_init__(self):
        if not self.UUID:
            self.UUID = str(uuid.uuid4())

    @property
    def props(self) -> dict:
        return {
            "UUID": self.UUID,
            "label": self.label,
            "locus": self.locus,
            "occurrences": ";".join(self.occurrences),
            "note": self.note,
            "is_bold": self.is_bold,
            "is_footnote": self.is_footnote
        }

    # Convert object properties into a string representing Neo4j property set (json without parentheses in keys)
    def serialize(self):
        return "{" + ', '.join('{0}: "{1}"'.format(key, value) for (key, value) in self.props.items()) + "}"

    # Restore object from a string representing Neo4j property set (json without parentheses in keys)
    @classmethod
    def deserialize(cls, props):
        self = cls(UUID=props["UUID"])
        if "occurrences" in props:
            setattr(self, "occurrences", props["occurrences"].split(";"))
            del props["occurrences"]
        for key in props.keys():
            setattr(self, key, props[key])
        return self


@dataclass_json
@dataclass
class IndexReference(BaseReference):
    """A class for holding information about an index"""
    refs: [IndexReferencePart] = None
    types: [str] = None

    # An argument to distinguish between parsing of index references in text vs index files
    inline: bool = False

    @property
    def props(self) -> dict:
        props = BaseReference.props.fget(self)
        props["types"] = ";".join(self.types)
        return props

    @classmethod
    def deserialize(cls, props):
        self = cls(UUID=props["UUID"])
        del props["text"]
        if "types" in props:
            setattr(self, "types", props["types"].split(";"))
            del props["types"]
        for key in props.keys():
            setattr(self, key, props[key])
        return self

    def parse(self):
        if not self.text:
            return
        self.text = self.text.replace("\n", " ")
        # TODO Can parsing benefit from special spacing?
        self.text = self.text.replace(" ", " ")
        self.text = self.text.replace(" ", " ")
        # print("Parsing index text as " + " or ".join(self.types) +": ", self.text)
        if len(self.text) < 5:
            print("Index text is too short", self.text)
            return
        if len(self.text) > 3000:
            print("Index text is too long", self.text)
            return
        if self.types:
            self.refs = []
            options = {
                "verborum": self.parse_as_verborum,
                "locorum":  self.parse_as_locorum,
                "nominum_ancient": self.parse_as_nominum_ancient,
                "nominum_modern": self.parse_as_nominum_modern,
                "rerum": self.parse_as_rerum,
                "geographicus": self.parse_as_geographicus,
                "bibliographicus": self.parse_as_bibliographicus,
                "epigraphic": self.parse_as_epigraphic
            }
            if len(self.types) > 0:
                if self.types[0] in options.keys():
                    options[self.types[0]]()
                else:
                    print("No parsers for this index type yet", ", ".join(self.types), self.text)
        # else:
        #     print("Unclassified index: ", self.text)

    def parse_as_locorum(self):
        try:
            if self.inline:
                return self.parse_locorum_inline()
            else:
                return self.parse_loop(self.parse_pattern1)
        except ParseException:
            print("Failed to parse index locorum: ", self.text)

    def parse_as_rerum(self):
        try:
            self.parse_loop(self.parse_pattern2)
        except ParseException:
            print("Failed to parse index rerum: ", self.text)

    def parse_as_nominum_ancient(self):
        try:
            ref = self.parse_pattern2(self.text)
            idx_ref = IndexReferencePart(label=" ".join(ref.label).strip(), occurrences=ref.occurrences, note=ref.rest)
            self.refs.append(idx_ref)
        except ParseException:
            print("Failed to parse index nominum (ancient): ", self.text)

    def parse_as_nominum_modern(self):
        try:
            ref = self.parse_pattern2(self.text)
            idx_ref = IndexReferencePart(label=" ".join(ref.label).strip(), occurrences=ref.occurrences, note=ref.rest)
            self.refs.append(idx_ref)
        except ParseException:
            print("Failed to parse index nominum (modern): ", self.text)

    def parse_as_verborum(self):
        try:
            self.parse_loop(self.parse_pattern2)
        except ParseException:
            print("Failed to parse index verborum: ", self.text)

    def parse_as_epigraphic(self):
        print("No parser for index epigraphic: ", self.text)

    def parse_as_geographicus(self):
        try:
            self.parse_loop(self.parse_pattern2)
        except ParseException:
            print("Failed to parse index geographicus: ", self.text)

    def parse_as_bibliographicus(self):
        print("No parser for index bibliographicus: ", self.text)

    def parse_loop(self, processor):
        text = self.text
        the_end = False
        while not the_end:
            ref = processor(text)
            label = " ".join(ref.label).strip()
            if label.endswith(','):
                label = label[:-1]
            idx_ref = IndexReferencePart(label=label, locus=ref.locus, occurrences=ref.occurrences)
            self.refs.append(idx_ref)
            text = ref.rest
            the_end = True if len(text) == 0 else False
            if the_end:
                idx_ref.note = text
        # print(self.refs)

    # @Examples:
    #   locorum: Adespota elegiaca (IEG)  23 206
    #     Aeschines 2.157 291
    def parse_pattern1(self, text):
        alphas=ppu.Latin1.alphas+ppu.LatinA.alphas+ppu.LatinB.alphas+ppu.Greek.alphas+"\"'.’-—:“”‘’&()/«»?"
        occurrences = delimitedList(Word(ppu.Latin1.nums), delim=",")
        locus_fragment = Word(ppu.Latin1.nums+".–=") + Optional(oneOf("ff."))
        locus = locus_fragment + Optional('/'+locus_fragment)
        label_chars = Word(alphas+',;')
        label = OneOrMore(label_chars.setParseAction(''.join))
        index = Optional(label("label")) + Optional(locus("locus").setParseAction(''.join) + occurrences('occurrences') + restOfLine("rest"))
        return index.parseString(text)

    # @Examples:
    #   rerum: Adonis (Plato Comicus), 160, 161, 207
    #   nominum: Antioch  10; 24; 79; 83; 85; 89–92;  105–107; 114–116; 118; 147–149; 152;  154–156; 173; 231
    def parse_pattern2(self, text):
        alphas=ppu.Latin1.alphas+ppu.LatinA.alphas+ppu.LatinB.alphas+ppu.Greek.alphas+"\"'.’-—:“”‘’&()/«»?"
        occurrences_chars=Word(ppu.Latin1.nums+'n–') + Optional(oneOf("f."))
        occurrences = OneOrMore(occurrences_chars + Optional(oneOf(", ;")).suppress())
        label_chars = Word(alphas+',;')
        label = OneOrMore(label_chars.setParseAction(''.join))
        # TODO generalize: after 'see' or 'see also' other index references with occurrences can appear
        alias = CaselessKeyword("see") + Optional(CaselessKeyword("also")) + delimitedList(Word(alphas), delim=oneOf(", ;"))
        # label.setName("label").setDebug()
        index = label("label") + Optional(occurrences("occurrences")) + Optional(alias("alias")) + restOfLine('rest')
        return index.parseString(text)

    # Inline pattern, only needed for testing
    def parse_locorum_inline(self):
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
            idx_ref = IndexReferencePart(label=" ".join(ref.label), locus=locus_txt)
            self.refs.append(idx_ref)
            print(idx_ref)

    @classmethod
    # Guess type of index. Can return several types
    # verborum - index of words
    # locorum  - index of references
    # nominum  - index of names
    # nominum_ancient - ancient people
    # nominum_modern  - modern authors
    # rerum    - index of subjects
    # geographicus - index of places
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
