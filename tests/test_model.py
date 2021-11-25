import unittest
from model.publication import Publication
from model.contributor import Contributor
from model.reference_bibliographic import Reference
from model.reference_index import IndexReference
from dataclasses import asdict
import json


class TestModel(unittest.TestCase):

    # Parse index locorum (occurence in the text)
    def test_index_locorum_inline_parser(self):
        idx = IndexReference("Hom. Il. 1,124-125", types=["locorum"], inline=True)
        self.assertEqual(idx.refs[0].label, "Hom. Il.")
        self.assertEqual("1.124-125", idx.refs[0].locus)

        idx = IndexReference("Hom. Il. 1,12-20; Verg. Aen., 2.240", types=["locorum"], inline=True)
        self.assertEqual("Hom. Il.", idx.refs[0].label)
        self.assertEqual("1.12-20", idx.refs[0].locus)
        self.assertEqual("Verg. Aen.", idx.refs[1].label)
        self.assertEqual("2.240", idx.refs[1].locus)

        idx = IndexReference("Hom. Il. 1,12-20; 2.240", types=["locorum"], inline=True)
        self.assertEqual("Hom. Il.", idx.refs[0].label)
        self.assertEqual("1.12-20", idx.refs[0].locus)
        self.assertEqual("", idx.refs[1].label)
        self.assertEqual("2.240", idx.refs[1].locus)

    # Parse index rerum
    def test_index_parser_pattern2(self):
        # Adonis (Plato Comicus), 160, 161, 207
        idx = IndexReference("Adonis (Plato Comicus), 160, 161, 207", types=["rerum"])
        self.assertEqual("Adonis (Plato Comicus)", idx.refs[0].label)
        self.assertEqual(3, len(idx.refs[0].occurrences))
        self.assertEqual("160", idx.refs[0].occurrences[0])
        self.assertEqual("207", idx.refs[0].occurrences[2])
        # actors, comic, 75, 78–82 disguising, 84–85 guilds, 92 Menander’s use of, 361–362 in performance, 116–119,
        # 137– 139 prizes, 137
        idx = IndexReference(("actors, comic, 75, 78–82 disguising, 84–85 guilds, 92 Menander’s use of, 361–362 in performance, "
                     "116–119, 137– 139 prizes, 137"), types=["verborum"])
        self.assertEqual("disguising", idx.refs[1].label)
        # Alberti, Leon Battista 86, 96–97, 99–100,  110, 221, 228, 244
        idx=IndexReference("Alberti, Leon Battista 86, 96–97, 99–100,  110, 221, 228, 244", types=["nominum_ancient"])
        self.assertEqual("Alberti, Leon Battista", idx.refs[0].label)
        # intention 15, 35–38, 85, 260, 272, 276,  288, 296, 299–306, 317, 331
        idx=IndexReference("intention 15, 35–38, 85, 260, 272, 276,  288, 296, 299–306, 317, 331", types=["verborum"])
        self.assertEqual("intention", idx.refs[0].label)
        # Pozzo, Andrea dal 192–193, 196n
        idx=IndexReference("Pozzo, Andrea dal 192–193, 196n", types=["nominum_ancient"])
        self.assertEqual("Pozzo, Andrea dal", idx.refs[0].label)
        # enumeration 155–166, 184 See also diversity; mathematics; point
        idx=IndexReference("enumeration 155–166, 184 See also diversity; mathematics; point", types=["verborum"])
        self.assertEqual("enumeration", idx.refs[0].label)
        self.assertEqual("155–166", idx.refs[0].occurrences[0])
        self.assertEqual("184", idx.refs[0].occurrences[1])
        # incompleteness 312–313 See also completeness; exhaustion
        idx = IndexReference("incompleteness 312–313 See also completeness; exhaustion", types=["verborum"])
        self.assertEqual("incompleteness", idx.refs[0].label)
        self.assertEqual("", idx.refs[0].note)
        idx = IndexReference(("Tyche,  30,  31,  44,  66,  67,  68,  72,  84,  85,  97,  105,  107,  lI5,  179,  180 " 
            "Valerianus,  16  Venus,  40,  42,  110,  147,  150,  151,  152,  157,  176,  185 "  
            "Vologoses  III,  13,  132 Wa'el,  131"), types=["verborum"])
        self.assertEqual("Tyche", idx.refs[0].label)

    # Parse index using pattern1
    def test_index_parser_pattern1(self):
        # Adespota elegiaca (IEG) 23 206
        idx = IndexReference("Adespota elegiaca (IEG) 23 206", types=["locorum"])
        self.assertEqual("Adespota elegiaca (IEG)", idx.refs[0].label)
        self.assertEqual("23", idx.refs[0].locus)
        self.assertEqual("206", idx.refs[0].occurrences[0])
        # Aeschines 2.157 291
        idx = IndexReference("Aeschines 2.157 291", types=["locorum"])
        self.assertEqual(idx.refs[0].label, "Aeschines")
        self.assertEqual(idx.refs[0].locus, "2.157")
        self.assertEqual(idx.refs[0].occurrences[0], "291")
        # Agamemnon 6–7 19
        idx = IndexReference("Agamemnon 6–7 19", types=["locorum"])
        self.assertEqual("Agamemnon", idx.refs[0].label)
        self.assertEqual("6–7", idx.refs[0].locus)
        self.assertEqual("19", idx.refs[0].occurrences[0])
        # Agamemnon 42–4 591, 593
        idx = IndexReference("Agamemnon 42–4 591, 593 ", types=["locorum"])
        self.assertEqual("Agamemnon", idx.refs[0].label)
        self.assertEqual("42–4", idx.refs[0].locus)
        self.assertEqual("591", idx.refs[0].occurrences[0])
        self.assertEqual("593", idx.refs[0].occurrences[1])
        # Aeschylus, Agamemnon (cont.)
        idx = IndexReference("Aeschylus, Agamemnon (cont.)", types=["locorum"])
        self.assertEqual("Aeschylus, Agamemnon (cont.)", idx.refs[0].label)
        self.assertEqual("", idx.refs[0].locus)
        # Aeschylus Agamemnon 203–4/216–17 433
        idx = IndexReference("Aeschylus Agamemnon 203–4/216–17 433", types=["locorum"])
        self.assertEqual("Aeschylus Agamemnon", idx.refs[0].label)
        self.assertEqual("203–4/216–17", idx.refs[0].locus)
        self.assertEqual("433", idx.refs[0].occurrences[0])
        # 204 454
        idx = IndexReference("204 454", types=["locorum"])
        self.assertEqual("204", idx.refs[0].locus)
        self.assertEqual("454", idx.refs[0].occurrences[0])
        # 204/217 326, 569, 670
        idx = IndexReference("204/217 326, 569, 670", types=["locorum"])
        self.assertEqual("204/217", idx.refs[0].locus)
        self.assertEqual("326", idx.refs[0].occurrences[0])
        self.assertEqual("569", idx.refs[0].occurrences[1])
        self.assertEqual("670", idx.refs[0].occurrences[2])
        # 219 ff. 58
        idx = IndexReference("219 ff. 58", types=["locorum"])
        self.assertEqual("219ff.", idx.refs[0].locus)
        self.assertEqual("58", idx.refs[0].occurrences[0])
        # 132 c.3 510
        # 447 ff./466 ff. 571
        # 346 fr.1 97, 433, 450, 506, 571, 744
        # fr. 3 585
        # Apollonius Rhodius 1. 570–1 273
        # Democritus (Diels–Kranz) 68 B 91 206
        # Ennius Tragedies (Jocelyn) fr. xcvi 62
        # 209/223a 680
        # Xenophanes (IEG) B 3 89
        # Xenophon Memorabilia 1. 5. 5 790

    # Parse multi-level locorum index text
    def test_index_locorum_parser_nested(self):
        complex_idx_text = ('Aeschylus Agamemnon 6–7 19 14 586 22 232, 410, 619 32 ff. 129 40 602 40–103 492 42–4 591, 593'
                          '43–4 57 48 130 60 591, 593 65 77 96 194 104 412 108–9 593, 799 108–9 / 126–7 415')
        nested_idx = IndexReference(complex_idx_text, types=["locorum"])
        self.assertEqual(15, len(nested_idx.refs))
        self.assertEqual("108–9/126–7", nested_idx.refs[14].locus)

    # Index is disambiguated via Hucitlib
    def test_query_hucitlib(self):
        from hucitlib import KnowledgeBase, HucitAuthor, HucitWork
        import pkg_resources
        virtuoso_cfg_file = pkg_resources.resource_filename('hucitlib', 'config/virtuoso.ini')
        kb = KnowledgeBase(virtuoso_cfg_file)
        kb.get_authors()
        res_aeschylus = kb.search('Aeschylus')
        res_agamemnon = kb.search('Agamemnon')
        self.assertGreaterEqual(len(res_aeschylus), 1)
        self.assertGreaterEqual(len(res_agamemnon), 1)
        author = res_aeschylus[0][1].to_json()
        author_data = json.loads(author)
        self.assertEqual(type(author_data), dict)
        names = [name["label"] for name in author_data["names"]]
        self.assertIn('Aeschylus', names)

    # Index is disambiguated via Hucitlib
    def test_disambiguate_index_author(self):
        from model.disambiguate_index import DisambiguateIndex
        ext_idx = DisambiguateIndex.find_author_hucitlib('Aeschylus')
        self.assertIsNotNone(ext_idx)

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

    # Parse bibliographic reference
    def test_reference_parser(self):
        data = [
            "C. Lane, Venise, une République maritime, Paris, 1988, p. 344;",
            "Lane, Frédéric Chapin. Venise : une république maritime, préface de Fernand Braudel; trail, de l'américain par Yannick Bourdoiseau et Marie Ymonel. Paris, Flammarion, coll. «Champs». 1988.",
            "Coulon, V., ed. 1923-1930. Aristophane, 5 vols., trans. H. van Daele. Paris"
        ]
        for ref_text in data:
            ref = Reference(ref_text)
            self.assertIsNotNone(ref.year)
            self.assertIsNotNone(ref.authors)
            self.assertIsNotNone(ref.title)
            # print(ref.authors, "#", ref.year, "#", ref.title)
        ref = Reference("D’Andria, F. “Scavi nella zona del Kerameikos.” (NSA Supplement 29: Metaponto I) 355-452")
        self.assertEqual("D’Andria, F.", "".join(ref.authors))
        self.assertEqual("Scavi nella zona del Kerameikos", ref.title)

    # Parse publication
    def test_publication_bib_parser(self):
        pub = Publication.from_zip('../data_test/9789004188846_BITS.zip', extract_bib=True)
        self.assertEqual(1236, len(pub.bib_refs))
        self.assertEqual('2003', pub.bib_refs[0].year)
        self.assertEqual('1987', pub.bib_refs[5].year)
        self.assertEqual(('Athena’s Epithets: Their Structural Significance in the Plays of '
                         'Aristophanes (Beiträge zur Altertumskunde 67)'), pub.bib_refs[10].title)
        self.assertIsNotNone(pub.UUID)
        pub.save("../tmp/9789004188846_BITS.pub")
        # pub_copy = Publication.load("../tmp/9789004188846_BITS.pub")
        # print(pub_copy)
        for author in pub.editors:
            x = json.dumps(asdict(author))
            y = Contributor.from_json(x)
            print(y)

    def test_props(self):
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
