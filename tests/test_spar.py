import unittest
from model.map_to_spar import MapToSpar
from model.reference_bibliographic import Reference
from model.publication import Publication
from model.db_connector import DBConnector
from model.disambiguate_bibliographic import DisambiguateBibliographic
import zipfile
import os


class TestMappingSPAR(unittest.TestCase):

    def test_translate_refs(self):
        # pub_zip = zipfile.ZipFile("../data_test/9789004188846_BITS.zip", 'r')
        # for file_name in pub_zip.namelist():
        #     if file_name.endswith('.xml'):
        #         jats_file = pub_zip.open(file_name)
        #         MapToSpar.jats_to_spar(jats_file)
        #         jats_file.close()
        # pub_zip.close()

        refs = []
        refs.append(Reference("D’Andria, F. “Scavi nella zona del Kerameikos.” (NSA Supplement 29: Metaponto I) 355-452", ref_num=1))
        refs.append(Reference(("Abadie-Reynal, C. and J.-P. Darmon. 2003. “La maison et la mosaïque des"
            "Synaristosai (Les femmes au déjeuner de Ménandre).” In Zeugma: Interim"
            "Reports (JRA Supplement 51), 79–99. Portsmouth, RI."), ref_num=2))
        refs.append(Reference(("Barral I Altet, Xavier. “Quelques observations sur les mosaïques de pavement,"
            "l’architecture, la liturgie et la symboliq"), ref_num=3))

        # for ref in refs:
        #     DisambiguateBibliographic.find_google_books(ref)
        #     DisambiguateBibliographic.find_crossref(ref)

        MapToSpar.translate_refs(refs)
        # MapToSpar.translate_pub(None)

    def test_translate_pub(self):
        pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
        self.assertIsNotNone(pwd)
        prefix = "data\\41a8cdce8aae605806c445f28971f623"
        db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", pwd)

        # Restore publication with bibliographic references
        db_pub = db.query_pub_by_zip(prefix + "\\9789004261648_BITS\\9789004261648_BITS.zip")
        self.assertIsNotNone(db_pub)
        db_pub = db.query_pub_full(db_pub.UUID)
        self.assertGreaterEqual(len(db_pub.authors), 1)
        self.assertGreaterEqual(len(db_pub.identifiers), 1)
        self.assertGreaterEqual(len(db_pub.bib_refs), 5)

        # Restore publication with index references
        db_pub1 = db.query_pub_by_zip(prefix + "\\9789004232402_BITS\\9789004232402_BITS.zip")
        self.assertIsNotNone(db_pub1)
        db_pub1 = db.query_pub_full(db_pub1.UUID)
        self.assertGreaterEqual(len(db_pub1.authors), 1)
        self.assertGreaterEqual(len(db_pub1.identifiers), 1)
        self.assertGreaterEqual(len(db_pub1.index_refs), 5)

        db.close()

        # db_pub.disambiguate_bib()
        MapToSpar.translate_pub(db_pub)
