import unittest
from model.publication import Publication
from model.contributor import Contributor
from model.reference_bibliographic import Reference
from model.reference_index import IndexReference
from dataclasses import asdict
import json
from model.db_connector import DBConnector
import os

# Set environment variables


class TestDBConnector(unittest.TestCase):

    def test_query_nodes(self):
        pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
        self.assertIsNotNone(pwd)
        db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", pwd)

        # Retrieve all publications
        db_pubs = db.query_pubs(20)
        self.assertGreaterEqual(len(db_pubs), 20)
        # Retrieve all references
        db_refs = db.query_bib_refs(100)
        self.assertGreaterEqual(len(db_refs), 100)
        # Retrieve all indices
        db_idx_refs = db.query_index_refs(100)
        self.assertGreaterEqual(len(db_idx_refs), 100)
        # Retrieve bibliographic references for a publication
        db_pub_refs = db.query_pub_bib_refs("43dd4ed2-f9d3-4ccf-9361-a897789e81fe")
        self.assertGreaterEqual(len(db_pub_refs), 1)
        print(db_pub_refs)
        # Retrieve index references for a publication
        db_pub_idx_refs = db.query_pub_index_refs("43dd4ed2-f9d3-4ccf-9361-a897789e81fe")
        self.assertGreaterEqual(len(db_pub_idx_refs), 1)
        print(db_pub_idx_refs)
        # # Find publication by zip_path (for update)
        # zip_file = '../data_test/9783657782116_BITS.zip'
        # pub = Publication.from_zip(zip_file, extract_bib=True, extract_index=True)
        # print(pub.zip_path)
        # db_pub = db.query_pubs_by_zip(pub.zip_path)
        # self.assertIsNotNone(db_pub)
        db.close()
