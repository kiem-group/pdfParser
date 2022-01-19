import unittest
from model.publication import Publication
from model.disambiguate_bibliographic import DisambiguateBibliographic
from model.reference_bibliographic import Reference
from urllib.parse import quote
import re
from model.log_config import config_logger
import csv


class TestRefBibParser(unittest.TestCase):

    def setUp(self):
        self.logger = config_logger("test_ref_bib_parser.log")

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

    # Disambiguate selected references
    def test_disambiguation(self):
        refs = [
            "Vernant, Jean - Pierre, Mythe et société en Grèce ancienne (Paris, 2004).",
            "Vernant, Jean - Pierre, Problèmes de la guerre en Grèce ancienne (Paris, 1999).",
            ("Vernant, Jean-Pierre, “One ... Two ... Three: Eros,” in Before Sexuality: "
                "The Construction of Erotic Experience in the Ancient Greek World, "
                "ed. Donald M. Halperin, John J. Winkler, and Froma I. Zeitlin (Princeton, 1999), 465-478."),
            "Syme, Ronald, The Roman Revolution (Oxford, 1939).",
            "Syme, R., The Roman Revolution (Oxford, 1960)."
        ]
        for ref in refs:
            parts = re.split('[;,()]', ref)
            title = max(parts, key=len)
            book_data = DisambiguateBibliographic.query_google_books(title, "")
            self.assertGreaterEqual(int(book_data['totalItems']), 1)

    # Query based on keywords + intitle should help to locate requested publication
    def test_google_api_format(self):
        ref = "The Brazen House. A Study of the Vestibule of the Imperial Palace of Constantinople"
        ext_text = "The Brazen House"
        ext = "&intitle:" + quote(ext_text)
        res = DisambiguateBibliographic.query_google_books(ref, ext)
        self.assertEqual(10, len(res["items"]))
        self.assertEqual("The Brazen House", res["items"][0]["volumeInfo"]["title"])

    # Disambiguation with OpenCitation API
    def test_query_open_citations_pub(self):
        pub = Publication.from_zip('./data_test/9789004188846_BITS.zip', extract_bib=True)
        print(len(pub.bib_refs))
        if pub.doi:
            res = DisambiguateBibliographic.query_open_citations(pub.doi)
            self.assertGreaterEqual(len(res), 3)

    # Estimation of success rate of disambiguation
    def test_evaluate_disambiguation(self):
        self.logger.info("Started test_evaluate_disambiguation")
        header = ["Reference", "GoogleAPI", "CrossRef", "HumanEvaluation", "HumanLink"]
        writer = csv.writer(open('../data_test/test_evaluate_disambiguation.csv', "w", encoding='utf-8', newline=""))
        writer.writerow(header)
        from model.db_connector import DBConnector
        import os
        pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
        db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", pwd)
        cql_refs = "MATCH (a:Reference) WHERE NOT a.authors STARTS WITH '—' return a, rand() as r ORDER BY r"
        num_refs = 500
        refs = db.query_resource(cql_refs, Reference, num_refs)
        success_google = 0
        success_crossref = 0
        count = 0
        for ref in refs:
            DisambiguateBibliographic.find_google_books(ref)
            DisambiguateBibliographic.find_crossref(ref)
            url_google = []
            url_crossref = []
            if ref.refers_to is not None:
                url_google = [e.url_google for e in ref.refers_to if e.url_google is not None]
                success_google += 1 if len(url_google) > 0 else 0
                url_crossref = [e.url_crossref for e in ref.refers_to if e.url_crossref is not None]
                success_crossref += 1 if len(url_crossref) > 0 else 0
            out_google = ", ".join(url_google)
            out_crossref = ", ".join(url_crossref)
            count += 1
            self.logger.info(str(count) + " " + ref.text + " " + out_google + " " + out_crossref)
            writer.writerow([ref.text, out_google, out_crossref])
        self.logger.info("Success rate (out of %s): %s, %s", num_refs, success_google, success_crossref)
        self.logger.info("Finished test_evaluate_disambiguation")


if __name__ == '__main__':
    unittest.main()
