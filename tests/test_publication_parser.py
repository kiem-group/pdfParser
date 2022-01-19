import unittest
from model.contributor import Contributor
from model.reference_index import IndexReference
from model.reference_bibliographic import Reference
from model.publication import Publication
from dataclasses import asdict
import json


class TestModel(unittest.TestCase):

    # Test whether publication information is correctly extracted from JATS
    def test_publication_parser(self):
        zip_file = '../data_test/9783657782116_BITS.zip'
        pub = Publication.from_zip(zip_file)
        self.assertEqual("ger", pub.lang)
        self.assertEqual("10.30965/9783657782116", pub.doi)
        self.assertEqual(['9783506782113', '9783657782116'], pub.isbn)
        self.assertIsNone(pub.issn)
        self.assertEqual('Prosper Tiro Chronik - Laterculus regum Vandalorum et Alanorum', pub.title)
        self.assertEqual(2, len(pub.editors))
        self.assertEqual(0, len(pub.authors))
        self.assertEqual('BRILL', pub.publisher)
        self.assertEqual('Netherlands', pub.location)
        self.assertEqual('2016', pub.year)
        self.assertEqual('../data_test/9783657782116_BITS.zip', pub.zip_path)

    # Parse publication
    def test_publication_bib_parser(self):
        pub = Publication.from_zip('../data_test/9789004188846_BITS.zip', extract_bib=True)
        # Check UUID
        self.assertIsNotNone(pub.UUID)
        # Check identifiers
        self.assertGreaterEqual(len(pub.identifiers), 1)
        self.assertEqual(pub.identifiers[0].format, 'print')
        self.assertEqual(pub.identifiers[0].type, 'issn')
        self.assertEqual(pub.identifiers[0].id, '1872-3357')
        # Check contributors
        self.assertGreaterEqual(len(pub.editors), 1)
        self.assertEqual(pub.editors[0].surname, 'Dobrov')
        self.assertEqual(pub.editors[0].given_names, 'Gregory W.')
        # Check bibliographic references
        self.assertEqual(1236, len(pub.bib_refs))
        self.assertEqual('2003', pub.bib_refs[0].year)
        self.assertEqual('1987', pub.bib_refs[5].year)
        self.assertEqual(('Athena’s Epithets: Their Structural Significance in the Plays of '
                         'Aristophanes (Beiträge zur Altertumskunde 67)'), pub.bib_refs[10].title)
        pub.save("../tmp/9789004188846_BITS.pub")
        # pub_copy = Publication.load("../tmp/9789004188846_BITS.pub")
        # print(pub_copy)
        for author in pub.editors:
            x = json.dumps(asdict(author))
            y = Contributor.from_json(x)
            self.assertEqual(y.surname, 'Dobrov')
            self.assertEqual(y.given_names, 'Gregory W.')

    # Check that generated uuid are distinct
    def test_resource_uuid(self):
        author = Contributor(UUID="3a9987f0-40c8-42d3-9ff8-24a5289ae978", type="author", surname="Smith", given_names="Mike")
        s = author.serialize()
        self.assertEqual('{type: "author", surname: "Smith", '
                         'given_names: "Mike", full_name: "None", UUID: "3a9987f0-40c8-42d3-9ff8-24a5289ae978"}', s)
        pub1 = Publication("Some book")
        pub2 = Publication("Some other book")
        self.assertNotEqual(pub1.UUID, pub2.UUID)
        ref1 = Reference("Some reference")
        ref2 = Reference("Some other reference")
        self.assertNotEqual(ref1.UUID, ref2.UUID)
        idx1 = IndexReference("Some index")
        idx2 = IndexReference("Some other index")
        self.assertNotEqual(idx1.UUID, idx2.UUID)


if __name__ == '__main__':
    unittest.main()
