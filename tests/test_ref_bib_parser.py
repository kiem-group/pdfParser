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
            "Coulon, V., ed. 1923-1930. Aristophane, 5 vols., trans. H. van Daele. Paris",
            "Brown,  P.  G.  M.  1983,  “Menander’s  dramatic  technique  and  the  law  of  Athens”,  Classical  Quarterly, vol. 33, pp. 412–420. "
            "Andrewes, A. 1961, “Philochoros on phratries”, Journal of Hellenic Studies, vol. 81, pp. 1–15. ",
            "——. 1994, “Legal space in classical Athens”, Greece and Rome, vol. 41, pp. 172–186. ",
            "Cobetto Ghiggia, P. 2002, Iseo: Contra Leocare (sulla successione di Diceogene) introduzione,  testo critico, traduzione e commento, Pisa. ",
            "De Jong, I. 2001, A narratological commentary on the Odyssey, Cambridge. ",
            "——. 1968b, Aristophanes Clouds, edited with introduction and commentary, Oxford. ",
            "Conf anapolis: Indiana University Press, 2005. Pp. 28–49. ",
            "Butler, Edward P. “Polytheism and Individuality in the Henadic Manifold.” Dionysius 23 (2005): 83–104. ",
            "HTAS In Tijdschrift voor Filosofie 45 (1983): 3–40. Engl. Trans. MyC "
        ]
        for ref_text in data:
            ref = Reference(ref_text)
            self.assertIsNotNone(ref.year)
            self.assertIsNotNone(ref.author)
            self.assertIsNotNone(ref.title)
        ref = Reference("D’Andria, F. “Scavi nella zona del Kerameikos.” (NSA Supplement 29: Metaponto I) 355-452")
        self.assertEqual("D’Andria, F.", ref.author)
        self.assertEqual("Scavi nella zona del Kerameikos", ref.title)

    # Disambiguate selected references via GoogleAPI
    def test_disambiguation_google(self):
        text_refs = [
            "Vernant, Jean - Pierre, Mythe et société en Grèce ancienne (Paris, 2004).",
            "Vernant, Jean - Pierre, Problèmes de la guerre en Grèce ancienne (Paris, 1999).",
            ("Vernant, Jean-Pierre, “One ... Two ... Three: Eros,” in Before Sexuality: "
                "The Construction of Erotic Experience in the Ancient Greek World, "
                "ed. Donald M. Halperin, John J. Winkler, and Froma I. Zeitlin (Princeton, 1999), 465-478."),
            "Syme, Ronald, The Roman Revolution (Oxford, 1939).",
            "Syme, R., The Roman Revolution (Oxford, 1960)."
        ]
        for text in text_refs:
            ref = Reference(text)
            book_data = DisambiguateBibliographic.query_google_books(ref.title, "")
            self.assertGreaterEqual(int(book_data['totalItems']), 1)

    # def test_disambiguation_worldcat_jstore(self):
    #     text_refs = [("Wallace, Daniel B.Granville Sharp’s Canon and Its Kin: Semantics and Significance."
    #              "New york: peter lang, 2009.")]
    #     for text in text_refs:
    #         ref = Reference(text)
    #           book_data = DisambiguateBibliographic.query_worldcat(ref.title)
    #           print(book_data)
    #         book_data1 = DisambiguateBibliographic.query_jstore(ref.title)
    #         print(book_data1)

    # Disambiguate selected references via Brill's catalogue
    def test_disambiguation_brill(self):
        text_refs = [
            "Gentili, B.: Theatrical Performances in the Ancient World: Hellenistic and Early Roman Theatre",
            "Shean, J.F.: , Soldiering for God: Christianity and the Roman army, Leiden 2010"]
        for text in text_refs:
            ref = Reference(text)
            DisambiguateBibliographic.find_brill(ref)
            self.assertGreaterEqual(len(ref.refers_to), 1)
            ext_pub = ref.refers_to[0]
            self.assertIsNotNone(ext_pub.title)
            self.assertIsNotNone(ext_pub.authors)
            self.assertIsNotNone(ext_pub.year)
            self.assertIsNotNone(ext_pub.location)
            self.assertIsNotNone(ext_pub.publisher)
            self.assertIsNotNone(ext_pub.url)
            self.assertGreaterEqual(len(ext_pub.identifiers), 1)

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
        if pub.doi:
            res = DisambiguateBibliographic.query_open_citations(pub.doi)
            self.assertGreaterEqual(len(res), 3)

    # Estimation of success rate of disambiguation
    def test_evaluate_disambiguation(self):
        self.logger.info("Started test_evaluate_disambiguation")
        header = ["Reference", "GoogleAPI", "CrossRef", "Brill", "HumanEvaluation", "HumanLink"]
        writer = csv.writer(open('../data_test/test_evaluate_disambiguation.csv', "w", encoding='utf-8', newline=""))
        writer.writerow(header)
        from model.db_connector import DBConnector
        import os
        pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
        db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", pwd)
        cql_refs = "MATCH (a:Reference) WHERE NOT a.author STARTS WITH '—' return a, rand() as r ORDER BY r"
        num_refs = 50
        refs = db.query_resource(cql_refs, Reference, num_refs)
        success_google = 0
        success_crossref = 0
        success_brill = 0
        count = 0
        for ref in refs:
            DisambiguateBibliographic.find_google_books(ref)
            DisambiguateBibliographic.find_crossref(ref)
            DisambiguateBibliographic.find_brill(ref)
            url_google = []
            url_crossref = []
            url_brill = []
            if ref.refers_to is not None:
                url_google = [e.url for e in ref.refers_to if e.url is not None and e.type == "google"]
                success_google += 1 if len(url_google) > 0 else 0
                url_crossref = [e.url for e in ref.refers_to if e.url is not None and e.type == "crossref"]
                success_crossref += 1 if len(url_crossref) > 0 else 0
                url_brill = [e.url for e in ref.refers_to if e.url is not None and e.type == "brill"]
                success_brill += 1 if len(url_brill) > 0 else 0
            out_google = ", ".join(url_google)
            out_crossref = ", ".join(url_crossref)
            out_brill = ", ".join(url_brill)
            count += 1
            # self.logger.info(str(count) + " " + ref.text + " " + out_google + " " + out_crossref)
            writer.writerow([ref.text, out_google, out_crossref, out_brill])
        self.logger.info("Success rate (out of %s): %s, %s, %s", num_refs, success_google, success_crossref, success_brill)
        self.logger.info("Finished test_evaluate_disambiguation")


if __name__ == '__main__':
    unittest.main()
