# author: Natallia Kokash, natallia.kokash@gmail.com
# Maps KIEM resources to SPAR ontologies
# Definition of publication references like in http://www.sparontologies.net/examples#biro_1

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from lxml import etree
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, DCTERMS

FABIO = Namespace('http://purl.org/spar/fabio')
CITO = Namespace('http://purl.org/spar/cito')
BIRO = Namespace('http://purl.org/spar/biro')
CO = Namespace('http://purl.org/co/')
FRBR = Namespace('http://purl.org/vocab/frbr/core#')
# TODO Need own namespace
KIEM = Namespace('http://brill.com/kiem')

g = Graph()
g.bind('fabio', FABIO)
g.bind('cito', CITO)
g.bind('biro', BIRO)
g.bind('co', CO)
g.bind('frbr', FRBR)
g.bind('kiem', KIEM)
g.namespace_manager.bind('', URIRef(KIEM))

# g.parse('../spar/fabio.xml')
# g.parse('../spar/cito.xml')
# g.parse('../spar/biro.xml')

@dataclass_json
@dataclass
class MapToSpar:
    # Why mapping from JATS to RDF does not work?
    @classmethod
    def jats_to_spar(cls, jats_file):
        dom = etree.parse(jats_file)
        xslt_file = open("../spar/transform/jats2spar.xsl")
        xslt = etree.parse(xslt_file.read())
        transform = etree.XSLT(xslt)
        new_dom = transform(dom)
        file = open("../spar/jats_test.txt", "w")
        file.write(etree.tostring(new_dom, pretty_print=True))

    # Maps publication
    # <http://dx.doi.org/10.1002/asi.21134> frbr:part :reference-list .
    @classmethod
    def translate_pub(cls, pub):
        doi = URIRef(pub.doi)
        ref_list = URIRef(KIEM + "reference-list")
        g.add((doi, FRBR.part, ref_list))
        if pub.bib_refs:
            cls.translate_refs(pub.bib_refs, ref_list, doi)

    # Maps reference list
    # :reference-list a biro:ReferenceList ;
    # co:firstItem :reference-1 ;
    # co:item :reference-1 ,..., :reference-i , :reference-j , ... :reference-n ;
    # co:lastItem :reference-n .
    @classmethod
    def translate_refs(cls, refs, ref_list=None, doi=None):
        if len(refs) < 1:
            return
        if doi is None:
            doi = URIRef("http://dx.doi.org/test")
        if ref_list is None:
            ref_list = URIRef(KIEM + "reference-list")
            g.add((doi, FRBR.part, ref_list))

        g.add((ref_list, RDF.type, BIRO.ReferenceList))
        ref_first = URIRef(KIEM + "reference-1")
        g.add((ref_list, CO.firstItem, ref_first))
        for idx, ref in enumerate(refs):
            ref_item = URIRef(KIEM + "reference-" + str(ref.ref_num))
            g.add((ref_list, CO.item, ref_item))
        ref_last = URIRef(KIEM + "reference-" + str(len(refs)))
        g.add((ref_list, CO.lastItem, ref_last))

        for idx, ref in enumerate(refs):
            cls.translate_ref(ref, ref_list, idx == len(refs)-1)

        # Test
        print(g.serialize())

    # Maps a bibliographic reference
    # @Example
    # :reference-i a co:ListItem ;
    #     co:itemContent :renear02 ;
    #     co:nextItem :reference-j .
    #
    # :renear02 a biro:BibliographicReference ;
    # dcterms:bibliographicCitation
    #     "Renear, A., Dubin, D. & Sperberg-McQueen,
    #     C.M. (2002). Towards a semantics for XML markup.
    #     In E. Mudson (Chair), Proceedings of the ACM
    #     Symposium on Document Engineering, (pp. 119-126).
    #     New York: ACM Press." ;
    # biro:references <http://dx.doi.org/10.1145/585058.585081> .
    @classmethod
    def translate_ref(cls, ref, ref_list, is_last=False):

        # Create abbreviation: first author or ref-[ref_num] + year
        ref_id_str = "ref-" + str(ref.ref_num)
        ref_list_item = URIRef(KIEM + "reference-" + str(ref.ref_num))
        ref_list_next = URIRef(KIEM + "reference-" + str(int(ref.ref_num) + 1))
        ref_id = Literal(ref_id_str)

        # co:ListItem
        g.add((ref_list_item, RDF.type, CO.ListItem))
        g.add((ref_list_item, CO.ItemContent, ref_id))
        if not is_last:
            g.add((ref_list_item, CO.NextItem, ref_list_next))

        # biro:BibliographicReference
        g.add((ref_id, RDF.type, BIRO.BibliographicReference))
        g.add((ref_id, DCTERMS.bibliographicCitation, Literal(ref.text)))
        # Optional biro:references - point to disambiguation links
        if ref.refers_to and ref.refers_to.url:
            g.add((ref.id, BIRO.References, URIRef(ref.refers_to.url)))

