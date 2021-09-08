import unittest
from publication import Publication
from index import Index


class TestModel(unittest.TestCase):

    @unittest.skip("Parse index locorum")
    def test_index_locorum_parser(self):
        idx = Index("Hom. Il. 1,124-125", types=["locorum"])
        self.assertEqual(idx.refs[0].work, "Hom. Il.")
        self.assertEqual(idx.refs[0].start, "1.124")
        self.assertEqual(idx.refs[0].end, "125")

        idx = Index("Hom. Il. 1,12-20; Verg. Aen., 2.240", types=["locorum"])
        self.assertEqual(idx.refs[0].work, "Hom. Il.")
        self.assertEqual(idx.refs[0].start, "1.12")
        self.assertEqual(idx.refs[0].end, "20")
        self.assertEqual(idx.refs[1].work, "Verg. Aen.")
        self.assertEqual(idx.refs[1].start, "2.240")
        self.assertEqual(idx.refs[1].end, "")

        idx = Index("Hom. Il. 1,12-20; 2.240", types=["locorum"])
        self.assertEqual(idx.refs[0].work, "Hom. Il.")
        self.assertEqual(idx.refs[0].start, "1.12")
        self.assertEqual(idx.refs[0].end, "20")
        self.assertEqual(idx.refs[1].work, "")
        self.assertEqual(idx.refs[1].start, "2.240")
        self.assertEqual(idx.refs[1].end, "")

    # @unittest.skip("Parse index rerum")
    def test_index_rerum_parser(self):
        idx = Index("Adonis (Plato Comicus), 160, 161, 207", types=["rerum"])
        self.assertEqual(idx.refs[0].work, "Adonis (Plato Comicus)")
        self.assertEqual(len(idx.refs[0].passages), 3)
        self.assertEqual(idx.refs[0].passages[0], '160')
        self.assertEqual(idx.refs[0].passages[2], '207')

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

    # @unittest.skip("Parse publication")
    def test_publication_bib_parser(self):
        pub = Publication('../data_test/9789004188846_BITS.zip', extract_bib=True)
        self.assertEqual(1218, len(pub.bib_refs))
        self.assertEqual('2003', pub.bib_refs[0].year)
        self.assertEqual('1987', pub.bib_refs[5].year)
        self.assertEqual('Athena’s Epithets: Their Structural Significance in the Plays of Aristophanes (Beiträge zur Altertumskunde 67)', pub.bib_refs[10].title)

#  Index structures from Matteo
#     {
#         "title": "INDEX LOCORUM",
#         "notes": "The more important discussions are indicated in bold. ",
#         "entries": [
#             {
#                 "label": "Adespota elegiaca (IEG)",
#                 "locus": "23",
#                 "occurrences": [
#                     {
#                         "page": "206",
#                         "in_footnote": false,
#                         "in_bold": false
#                     }
#                 ]
#             },
#             {
#                 "label": "Aeschines",
#                 "loci": [
#                     {
#                         "locus": "2. 157",
#                         "occurrences": [
#                             {
#                                 "page": "291",
#                                 "in_footnote": true,
#                                 "in_bold": true
#                             }
#                         ]
#                     }
#                 ]
#             },
#             {
#                 "label": "Aeschylus, Agamemnon (cont.) ",
#                 "loci": [
#                     {
#                         "locus": "1410",
#                         "occurrences": [
#                             {
#                                 "page": "287"
#                             },
#                             {
#                                 "page": "335"
#                             },
#                             {
#                                 "page": "548"
#                             },
#                             {
#                                 "page": "652"
#                             },
#                             {
#                                 "page": "791"
#                             }
#                         ]
#                     },
#                     {
#                         "locus": "158–9/165–6",
#                         "occurrences": [
#                             {
#                                 "page": "290"
#                             },
#                             {
#                                 "page": "448"
#                             },
#                             {
#                                 "page": "565"
#                             }
#                         ]
#                     }
#                 ]
#             }
#         ]
#     }

# {
#     "title": "INDEX RERUM",
#     "notes": null,
#     "entries": [
#         {
#             "label": "administration financière",
#             "locus": null,
#             "occurrences": [
#                 {
#                     "page": "98"
#                 },
#                 {
#                     "page": "104"
#                 },
#                 {
#                     "page": "106"
#                 },
#             ]
#         },
#         {
#             "label": "conciles",
#             "locus": null,
#             "occurrences": [
#                 {
#                     "page": "126"
#                 },
#                 {
#                     "page": "129"
#                 },
#                 {
#                     "page": "130"
#                 }
#             ],
#             "entries":[
#                 {
#                     "label": "Chalcédonie (concile de, 451)",
#                     "locus": null,
#                     "occurrences": [
#                         {
#                             "page": "139"
#                         },
#                         {
#                             "page": "144"
#                         },
#                         {
#                             "page": "146"
#                         }
#                     ],
#                 }
#             ]
#         }
#     ]
# }


if __name__ == '__main__':
    unittest.main()
