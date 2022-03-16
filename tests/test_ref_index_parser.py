import unittest
from model.reference_index import IndexReference
from model.batch import Batch
from model.disambiguate_index import DisambiguateIndex
from model.log_config import config_logger
import csv


class TestIndexParser(unittest.TestCase):

    def setUp(self):
        self.logger = config_logger("test_ref_idx_parser.log")

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
    def test_disambiguate_index_hucitlib(self):
        self.logger.info("Testing Hucitlib...")
        ext_idx = DisambiguateIndex.query_hucitlib('Omero')
        self.assertIsNotNone(ext_idx)
        ext_idx = DisambiguateIndex.query_hucitlib('Aeschylus')
        self.assertIsNotNone(ext_idx)
        ext_idx = DisambiguateIndex.query_hucitlib('Agamemnon')
        self.assertIsNotNone(ext_idx)
        ext_idx = DisambiguateIndex.query_hucitlib("Jesus")
        self.assertIsNotNone(ext_idx)

    # Index is disambiguated via Wikidata
    def test_disambiguate_index_wikidata(self):
        self.logger.info("Testing Wikidata...")
        ext_idx = DisambiguateIndex.query_wikidata('Aeschylus')
        self.assertIsNotNone(ext_idx)
        self.assertEqual(ext_idx.uri, "www.wikidata.org/wiki/Q40939")
        ext_idx = DisambiguateIndex.query_wikidata('Agamemnon')
        self.assertIsNotNone(ext_idx)
        ext_idx = DisambiguateIndex.query_wikidata("Omero")
        self.assertIsNotNone(ext_idx)
        ext_idx = DisambiguateIndex.query_wikidata('No-entry-rubbish-text')
        self.assertIsNone(ext_idx)

    # Parsing of indices from zipped pdf files
    def test_extract_and_parse_indices(self):
        batch = Batch.from_zip('data/41a8cdce8aae605806c445f28971f623.zip', extract_index=True, extract_bib=False, size=5)
        index_count = [0, 335, 14, 30, 100]
        for idx, pub in enumerate(batch.publications):
            self.assertEqual(len(pub.index_refs), index_count[idx])
        batch.cluster()
        index_clusters = [cluster for cluster in batch.cluster_set_index.clusters if len(cluster.refs) > 1]
        self.assertGreaterEqual(len(index_clusters), 5)

    # Estimation of success rate of disambiguation
    def test_evaluate_index_disambiguation(self):
        self.logger.info("Started test_evaluate_index_disambiguation")
        header = ["Reference", "Labels", "Wikidata", "HumanEvaluation", "HumanLink"]
        with open('../data_test/test_evaluate_idx_disambiguation_labels.csv', "w", encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            from model.db_connector import DBConnector
            import os
            pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
            db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", pwd)
            cql_refs = "MATCH (a:IndexReference) WHERE a.types CONTAINS 'locorum' OR a.types CONTAINS 'nominum' " \
                       "return a, rand() as r ORDER BY r"
            idx_refs = db.query_resource(cql_refs, IndexReference, 500)
            success_wikidata = 0
            count = 0
            self.logger.debug("Indices restored, starting disambiguation...")
            for idx in idx_refs:
                idx.refers_to = []
                url_wikidata = []
                # Searching for labels and revised labels
                terms = idx.labels_ext
                for term in terms:
                    self.logger.debug("Searching for: %s", term)
                    ext = DisambiguateIndex.query_wikidata(term)
                    if ext:
                        idx.refers_to.append(ext)
                if idx.refers_to is not None:
                    url_wikidata = [e.uri for e in idx.refers_to if e.uri is not None]
                    success_wikidata += 1 if len(url_wikidata) > 0 else 0
                out_wikidata = " \n".join(url_wikidata)
                count += 1
                self.logger.info(str(count) + " (" + ", ".join(terms) + ") " + out_wikidata)
                writer.writerow([idx.text, " \n".join(terms), out_wikidata])
            self.logger.info("Success rate: %s/500", success_wikidata)
            self.logger.info("Finished test_evaluate_index_disambiguation")


if __name__ == '__main__':
    unittest.main()
