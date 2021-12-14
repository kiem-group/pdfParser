import unittest
from model.publication import Publication
from model.db_connector import DBConnector
import os


class TestDBConnector(unittest.TestCase):

    def test_query_nodes(self):
        pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
        self.assertIsNotNone(pwd)
        db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", pwd)

        # Retrieve all publications
        db_pubs = db.query_pubs(20)
        for p in db_pubs:
            print(p.UUID, p.zip_path)
        self.assertGreaterEqual(len(db_pubs), 20)

        db_pub = db.query_pub_by_zip("data\\41a8cdce8aae605806c445f28971f623\\9783657782116_BITS\\9783657782116_BITS.zip")
        self.assertIsNotNone(db_pub)

        # Add publication
        # pub = Publication.from_zip('../data_test/9789004188846_BITS.zip', extract_bib=True, extract_index=True)
        # # pub.disambiguate_bib()
        # pub.disambiguate_index()
        # found_idx = [idx for idx in pub.index_refs if len(idx.refers_to) > 0]
        # print(len(found_idx))
        #
        # db.create_pub(pub)
        # # Make sure publication was added
        # db_pub = db.query_pub(pub.UUID)
        # self.assertIsNotNone(db_pub)
        # # Find publication by zip_path
        # db_pub = db.query_pub_by_zip(pub.zip_path)
        # self.assertIsNotNone(db_pub)
        #
        # # Retrieve all references
        # db_refs = db.query_bib_refs(100)
        # self.assertGreaterEqual(len(db_refs), 100)
        # # Retrieve all indices
        # db_idx_refs = db.query_index_refs(100)
        # self.assertGreaterEqual(len(db_idx_refs), 100)
        #
        # # Retrieve bibliographic references for a publication
        # db_pub_refs = db.query_pub_bib_refs(pub.UUID)
        # self.assertEqual(len(db_pub_refs), len(pub.bib_refs))
        # # Retrieve index references for a publication
        # db_pub_idx_refs = db.query_pub_index_refs(pub.UUID)
        # self.assertEqual(len(db_pub_idx_refs), len(pub.index_refs))
        #
        # # TODO Test external references
        # # TODO Test clusters
        #
        # # Delete test publication
        # db.delete_pub(pub)
        #
        # # Make sure publication was deleted
        # db_pub = db.query_pub(pub.UUID)
        # self.assertIsNone(db_pub)

        db.close()
