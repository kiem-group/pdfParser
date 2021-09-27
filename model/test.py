import unittest
from publication import Publication
from index import Index


class TestModel(unittest.TestCase):

    @unittest.skip("Parse index locorum (occurence in the text)")
    def test_index_locorum_inline_parser(self):
        idx = Index("Hom. Il. 1,124-125", types=["locorum"], inline=True)
        self.assertEqual(idx.refs[0].label, "Hom. Il.")
        self.assertEqual("1.124-125", idx.refs[0].locus)

        idx = Index("Hom. Il. 1,12-20; Verg. Aen., 2.240", types=["locorum"],  inline=True)
        self.assertEqual("Hom. Il.", idx.refs[0].label)
        self.assertEqual("1.12-20", idx.refs[0].locus)
        self.assertEqual("Verg. Aen.", idx.refs[1].label)
        self.assertEqual("2.240", idx.refs[1].locus)

        idx = Index("Hom. Il. 1,12-20; 2.240", types=["locorum"],  inline=True)
        self.assertEqual("Hom. Il.", idx.refs[0].label)
        self.assertEqual("1.12-20", idx.refs[0].locus)
        self.assertEqual("", idx.refs[1].label)
        self.assertEqual("2.240", idx.refs[1].locus)

    # @unittest.skip("Parse index rerum")
    def test_index_parser_pattern2(self):
        # Adonis (Plato Comicus), 160, 161, 207
        idx = Index("Adonis (Plato Comicus), 160, 161, 207", types=["rerum"])
        self.assertEqual("Adonis (Plato Comicus)", idx.refs[0].label)
        self.assertEqual(3, len(idx.refs[0].occurrences))
        self.assertEqual("160", idx.refs[0].occurrences[0])
        self.assertEqual("207", idx.refs[0].occurrences[2])
        # actors, comic, 75, 78–82 disguising, 84–85 guilds, 92 Menander’s use of, 361–362 in performance, 116–119,
        # 137– 139 prizes, 137
        idx = Index(("actors, comic, 75, 78–82 disguising, 84–85 guilds, 92 Menander’s use of, 361–362 in performance, "
                     "116–119, 137– 139 prizes, 137"), types=["verborum"])
        self.assertEqual("disguising", idx.refs[1].label)
        # Alberti, Leon Battista 86, 96–97, 99–100,  110, 221, 228, 244
        idx=Index("Alberti, Leon Battista 86, 96–97, 99–100,  110, 221, 228, 244", types=["nominum_ancient"])
        self.assertEqual("Alberti, Leon Battista", idx.refs[0].label)
        # intention 15, 35–38, 85, 260, 272, 276,  288, 296, 299–306, 317, 331
        idx=Index("intention 15, 35–38, 85, 260, 272, 276,  288, 296, 299–306, 317, 331", types=["verborum"])
        self.assertEqual("intention", idx.refs[0].label)
        # Pozzo, Andrea dal 192–193, 196n
        idx=Index("Pozzo, Andrea dal 192–193, 196n", types=["nominum_ancient"])
        self.assertEqual("Pozzo, Andrea dal", idx.refs[0].label)
        # enumeration 155–166, 184 See also diversity; mathematics; point
        idx=Index("enumeration 155–166, 184 See also diversity; mathematics; point", types=["verborum"])
        self.assertEqual("enumeration", idx.refs[0].label)
        self.assertEqual("155–166", idx.refs[0].occurrences[0])
        self.assertEqual("184", idx.refs[0].occurrences[1])
        # incompleteness 312–313 See also completeness; exhaustion
        idx = Index("incompleteness 312–313 See also completeness; exhaustion", types=["verborum"])
        self.assertEqual("incompleteness", idx.refs[0].label)
        self.assertEqual("", idx.refs[0].note)
        idx = Index(("Tyche,  30,  31,  44,  66,  67,  68,  72,  84,  85,  97,  105,  107,  lI5,  179,  180 " 
            "Valerianus,  16  Venus,  40,  42,  110,  147,  150,  151,  152,  157,  176,  185 "  
            "Vologoses  III,  13,  132 Wa'el,  131"), types=["verborum"])
        self.assertEqual("Tyche", idx.refs[0].label)

    def test_index_parser_pattern1(self):
        # Adespota elegiaca (IEG) 23 206
        idx = Index("Adespota elegiaca (IEG) 23 206", types=["locorum"])
        self.assertEqual("Adespota elegiaca (IEG)", idx.refs[0].label)
        self.assertEqual("23", idx.refs[0].locus)
        self.assertEqual("206", idx.refs[0].occurrences[0])
        # Aeschines 2.157 291
        idx = Index("Aeschines 2.157 291", types=["locorum"])
        self.assertEqual(idx.refs[0].label, "Aeschines")
        self.assertEqual(idx.refs[0].locus, "2.157")
        self.assertEqual(idx.refs[0].occurrences[0], "291")
        # Agamemnon 6–7 19
        idx = Index("Agamemnon 6–7 19", types=["locorum"])
        self.assertEqual("Agamemnon", idx.refs[0].label)
        self.assertEqual("6–7", idx.refs[0].locus)
        self.assertEqual("19", idx.refs[0].occurrences[0])
        # Agamemnon 42–4 591, 593
        idx = Index("Agamemnon 42–4 591, 593 ", types=["locorum"])
        self.assertEqual("Agamemnon", idx.refs[0].label)
        self.assertEqual("42–4", idx.refs[0].locus)
        self.assertEqual("591", idx.refs[0].occurrences[0])
        self.assertEqual("593", idx.refs[0].occurrences[1])
        # Aeschylus, Agamemnon (cont.)
        idx = Index("Aeschylus, Agamemnon (cont.)", types=["locorum"])
        self.assertEqual("Aeschylus, Agamemnon (cont.)", idx.refs[0].label)
        self.assertEqual("", idx.refs[0].locus)
        # Aeschylus Agamemnon 203–4/216–17 433
        idx = Index("Aeschylus Agamemnon 203–4/216–17 433", types=["locorum"])
        self.assertEqual("Aeschylus Agamemnon", idx.refs[0].label)
        self.assertEqual("203–4/216–17", idx.refs[0].locus)
        self.assertEqual("433", idx.refs[0].occurrences[0])
        # 204 454
        idx = Index("204 454", types=["locorum"])
        self.assertEqual("204", idx.refs[0].locus)
        self.assertEqual("454", idx.refs[0].occurrences[0])
        # 204/217 326, 569, 670
        idx = Index("204/217 326, 569, 670", types=["locorum"])
        self.assertEqual("204/217", idx.refs[0].locus)
        self.assertEqual("326", idx.refs[0].occurrences[0])
        self.assertEqual("569", idx.refs[0].occurrences[1])
        self.assertEqual("670", idx.refs[0].occurrences[2])
        # 219 ff. 58
        idx = Index("219 ff. 58", types=["locorum"])
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

    # @unittest.skip("Multi-level locorum, skip for now")
    def test_index_locorum_parser_nested(self):
        complex_idx_text=('Aeschylus Agamemnon 6–7 19 14 586 22 232, 410, 619 32 ff. 129 40 602 40–103 492 42–4 591, 593'
                          '43–4 57 48 130 60 591, 593 65 77 96 194 104 412 108–9 593, 799 108–9 / 126–7 415')
        nested_idx = Index(complex_idx_text, types=["locorum"])
        self.assertEqual(15, len(nested_idx.refs))
        self.assertEqual("108–9/126–7", nested_idx.refs[14].locus)

    @unittest.skip("Test whether publication information is correctly extracted from JATS")
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

    @unittest.skip("Parse publication")
    def test_publication_bib_parser(self):
        pub = Publication('../data_test/9789004188846_BITS.zip', extract_bib=True)
        self.assertEqual(1218, len(pub.bib_refs))
        self.assertEqual('2003', pub.bib_refs[0].year)
        self.assertEqual('1987', pub.bib_refs[5].year)
        self.assertEqual('Athena’s Epithets: Their Structural Significance in the Plays of Aristophanes (Beiträge zur Altertumskunde 67)', pub.bib_refs[10].title)



if __name__ == '__main__':
    unittest.main()
