# author: Natallia Kokash, natallia.kokash@gmail.com
# Maps KIEM resources to SPAR ontologies
# Definition of publication references like in http://www.sparontologies.net/examples#biro_1

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from lxml import etree
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF

FABIO = Namespace('http://purl.org/spar/fabio')
CITO = Namespace('http://purl.org/spar/cito')
BIRO = Namespace('http://purl.org/spar/biro')
CO = Namespace('http://purl.org/co/')
FRBR = Namespace('http://purl.org/vocab/frbr/core#')
c4o = Namespace('http://purl.org/spar/c4o')
KIEM = Namespace('http://brill.com/kiem/')
DOI = "http://dx.doi.org/"


@dataclass_json
@dataclass
class MapToSpar:

    def __post_init__(self):
        self.g = Graph()
        self.g.bind('fabio', FABIO)
        self.g.bind('cito', CITO)
        self.g.bind('biro', BIRO)
        self.g.bind('co', CO)
        self.g.bind('frbr', FRBR)
        self.g.bind('kiem', KIEM)
        self.g.namespace_manager.bind('', URIRef(KIEM))

    # Maps publication
    # <http://dx.doi.org/10.1002/asi.21134> frbr:part :reference-list .
    def translate_pub(self, pub):
        # Brill publications contain just ID in the field doi
        if not pub.doi.startswith(DOI):
            doi = URIRef(DOI + pub.doi)
        else:
            doi = URIRef(pub.doi)
        ref_list = URIRef(KIEM + "reference-list")
        self.g.add((doi, FRBR.part, ref_list))
        if pub.bib_refs:
            self.translate_refs(pub.bib_refs, ref_list, doi)

    # Maps reference list
    # :reference-list a biro:ReferenceList ;
    # co:firstItem :reference-1 ;
    # co:item :reference-1 ,..., :reference-i , :reference-j , ... :reference-n ;
    # co:lastItem :reference-n .
    def translate_refs(self, refs, ref_list=None, doi=None):
        if len(refs) < 1:
            return
        if doi is None:
            doi = URIRef("http://dx.doi.org/test")
        if ref_list is None:
            ref_list = URIRef(KIEM + "reference-list")
            self.g.add((doi, FRBR.part, ref_list))
        self.g.add((ref_list, RDF.type, BIRO.ReferenceList))
        ref_first = URIRef(KIEM + "reference-1")
        self.g.add((ref_list, CO.firstItem, ref_first))
        for idx, ref in enumerate(refs):
            id_str = '{:03d}'.format(ref.ref_num)
            ref_item = URIRef(KIEM + "reference-" + id_str)
            self.g.add((ref_list, CO.item, ref_item))
        id_str_last = '{:03d}'.format(len(refs) + 1)
        ref_last = URIRef(KIEM + "reference-" + id_str_last)
        self.g.add((ref_list, CO.lastItem, ref_last))
        for idx, ref in enumerate(refs):
            self.translate_ref(ref, idx == len(refs)-1)

    # Maps a bibliographic reference
    def translate_ref(self, ref, is_last=False):
        # Create abbreviation: first author or ref-[ref_num] + year
        id_str = '{:03d}'.format(ref.ref_num)
        id_str_next = '{:03d}'.format(int(ref.ref_num) + 1)

        ref_id_str = "ref-" + id_str
        ref_id = URIRef(KIEM + ref_id_str)
        ref_list_item = URIRef(KIEM + "reference-" + id_str)
        ref_list_next = URIRef(KIEM + "reference-" + id_str_next)
        # co:ListItem
        self.g.add((ref_list_item, RDF.type, CO.ListItem))
        self.g.add((ref_list_item, CO.itemContent, ref_id))
        if not is_last:
            self.g.add((ref_list_item, CO.nextItem, ref_list_next))
        # biro:BibliographicReference
        self.g.add((ref_id, RDF.type, BIRO.BibliographicReference))
        self.g.add((ref_id, c4o.hasContent, Literal(ref.text)))
        # Optional biro:references - point to disambiguation links
        if ref.refers_to and ref.refers_to:
            for ext_pub in ref.refers_to:
                self.g.add((ref.id, BIRO.References, URIRef(ext_pub.url)))

    # Save graph to the file
    def save(self, out_path: str):
        out = open(out_path, "w", encoding='utf-8')
        out.write(self.g.serialize())
        out.close()
