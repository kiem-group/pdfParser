import unittest
from model.publication import Publication
from model.db_connector import DBConnector
from model.log_config import config_logger
import os


class TestDBConnector(unittest.TestCase):

    def setUp(self):
        self.pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
        self.assertIsNotNone(self.pwd)
        self.db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", self.pwd)
        self.logger = config_logger()

    def test_query_nodes(self):
        # Retrieve 20 publications
        db_pubs = self.db.query_pubs(20)
        self.assertEqual(len(db_pubs), 20)
        # Retrieve 100 references
        db_refs = self.db.query_bib_refs(100)
        self.assertGreaterEqual(len(db_refs), 100)
        # Retrieve 100 indices
        db_idx_refs = self.db.query_index_refs(100)
        self.assertGreaterEqual(len(db_idx_refs), 100)

        node_count_before = self.db.query_node_count()
        rel_count_before = self.db.query_rel_count()

        # Create and add publication
        data_dir = "data\\41a8cdce8aae605806c445f28971f623\\"
        data_test_dir = "..\\data_test\\"
        pub_dir = "9783657782116_BITS" # 9789004188846_BITS
        pub_zip = data_dir + pub_dir + "\\" + pub_dir + ".zip"

        self.logger.info("Creating test publication: " + pub_zip)

        db_pub = self.db.query_pub_by_zip(pub_zip)
        self.assertIsNotNone(db_pub)

        pub = Publication.from_zip(data_test_dir + pub_dir + '.zip', extract_bib=True, extract_index=True)

        pub.disambiguate_bib()
        found_bib = [bib for bib in pub.bib_refs if len(bib.refers_to) > 0]
        self.logger.info("Disambiguated bibliographic references (#): " + str(len(found_bib)))

        pub.disambiguate_index()
        found_idx = [idx for idx in pub.index_refs if len(idx.refers_to) > 0]
        self.logger.info("Disambiguated index references (#): " + str(len(found_idx)))

        self.db.create_pub(pub)

        # Make sure publication was added
        db_pub = self.db.query_pub(pub.UUID)
        self.assertIsNotNone(db_pub)
        # Find publication by zip_path
        db_pub = self.db.query_pub_by_zip(pub.zip_path)
        self.assertIsNotNone(db_pub)
        node_count_plus = self.db.query_node_count()
        rel_count_plus = self.db.query_rel_count()
        self.assertGreater(node_count_plus, node_count_before)
        self.assertGreater(rel_count_plus, rel_count_before)

        # Retrieve bibliographic references for a publication
        db_pub_refs = self.db.query_pub_bib_refs(pub.UUID)
        self.assertEqual(len(db_pub_refs), len(pub.bib_refs))
        # Retrieve index references for a publication
        db_pub_idx_refs = self.db.query_pub_index_refs(pub.UUID)
        self.assertEqual(len(db_pub_idx_refs), len(pub.index_refs))

        # # TODO Test external references
        # # TODO Test clusters

        # Delete test publication
        self.db.delete_pub(pub)

        # Make sure publication was deleted
        db_pub = self.db.query_pub(pub.UUID)
        self.assertIsNone(db_pub)
        node_count_after = self.db.query_node_count()
        rel_count_after = self.db.query_rel_count()
        self.assertEqual(node_count_after, node_count_before)
        self.assertEqual(rel_count_after, rel_count_before)

    def test_query_count(self):
        node_count = self.db.query_node_count()
        rel_count = self.db.query_rel_count()
        self.assertGreaterEqual(node_count, 10215)
        self.assertGreaterEqual(rel_count, 10108)

