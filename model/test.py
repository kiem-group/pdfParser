import unittest
from publication import Publication
from index import Index


class TestModel(unittest.TestCase):

    @unittest.skip("Testing index parser")
    def test_index_parser(self):
        idx = Index("Hom. Il. 1,124-125")
        self.assertEqual(idx.refs[0].work, "Hom. Il.")
        self.assertEqual(idx.refs[0].start, "1.124")
        self.assertEqual(idx.refs[0].end, "125")

        idx = Index("Hom. Il. 1,12-20; Verg. Aen., 2.240")
        self.assertEqual(idx.refs[0].work, "Hom. Il.")
        self.assertEqual(idx.refs[0].start, "1.12")
        self.assertEqual(idx.refs[0].end, "20")
        self.assertEqual(idx.refs[1].work, "Verg. Aen.")
        self.assertEqual(idx.refs[1].start, "2.240")
        self.assertEqual(idx.refs[1].end, "")

        idx = Index("Hom. Il. 1,12-20; 2.240")
        self.assertEqual(idx.refs[0].work, "Hom. Il.")
        self.assertEqual(idx.refs[0].start, "1.12")
        self.assertEqual(idx.refs[0].end, "20")
        self.assertEqual(idx.refs[1].work, "")
        self.assertEqual(idx.refs[1].start, "2.240")
        self.assertEqual(idx.refs[1].end, "")

    # @unittest.skip("Test whether publication information is correctly extracted from JATS")
    def test_publication_parser(self):
        zip_file = '../data_test/9783657782116_BITS.zip'
        pub = Publication(zip_file)
        self.assertEqual("ger", pub.lang)
        self.assertEqual("10.30965/9783657782116", pub.doi)
        self.assertEqual('Prosper Tiro Chronik - Laterculus regum Vandalorum et Alanorum', pub.title)
        self.assertEqual(2, len(pub.editors))
        self.assertEqual(0, len(pub.authors))
        self.assertEqual('BRILL', pub.publisher)
        self.assertEqual('Netherlands', pub.location)
        self.assertEqual('2016', pub.year)
        self.assertEqual('../data_test/9783657782116_BITS.zip', pub.zip_path)
        self.assertEqual(9, len(pub.files))

    # @unittest.skip("Random selection of references for evaluation of disambiguation")
    def test_publication_bib_parser(self):
        pub = Publication('../data_test/9789004188846_BITS.zip', extract_bib=True)
        self.assertEqual(1218, len(pub.bib_refs))
        self.assertEqual('2003', pub.bib_refs[0].year)
        self.assertEqual('1987', pub.bib_refs[5].year)
        self.assertEqual('Athena’s Epithets: Their Structural Significance in the Plays of Aristophanes (Beiträge zur Altertumskunde 67)', pub.bib_refs[10].title)


if __name__ == '__main__':
    unittest.main()
