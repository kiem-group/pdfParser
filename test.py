import unittest
import csv
import re
from clustering import get_clustered_refs_flat
import Levenshtein
from model.reference_bibliographic import Reference
from disambiguation import query_google_books, query_crossref_pub, \
    disambiguate_google_books, disambiguate_crossref
from urllib.parse import quote


class TestClassifier(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestClassifier, cls).setUpClass()

    @unittest.skip("Random selection of references from file for evaluation of disambiguation")
    def test_random_pick_from_file(self):
        import random
        data = get_clustered_refs_flat('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
        validRefs = []
        for text in data:
            ref = Reference(text)
            if ref.authors and ref.year and ref.title:
                validRefs.append(ref)
        samples = random.sample(validRefs, 500)
        header = ["Reference", "CrossRef", "GoogleAPI", "Brill", "Other", "Remarks"]
        with open('data_test/ref_sample_disambiguation_eval.csv', "w", encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for sample in samples:
                writer.writerow([sample.text.strip()])

    @unittest.skip("Random selection of references from zipped pdf files for evaluation of disambiguation")
    def test_random_pick(self):
        import random
        from parser_corpus import parse_corpus
        corpus_list = parse_corpus('data')
        corpus = corpus_list[0]
        validRefs = []
        for pub in corpus.publications:
            if pub.bib_refs:
                for ref in pub.bib_refs:
                    if ref.authors and ref.year and ref.title:
                        validRefs.append(ref)
        samples = random.sample(validRefs, 500)
        header = ["Reference", "Cited_by_doi", "Cited_by_zip", "Cited_num", "CrossRef", "GoogleAPI", "Brill", "Other",
                  "Remarks"]
        with open('data_test/ref_sample_disambiguation_eval_new.csv', "w", encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for sample in samples:
                writer.writerow([sample.text.strip(), sample.cited_by_doi, sample.cited_by_zip, sample.ref_num])

    # @unittest.skip("Accuracy of reference clustering based on Levenshtein distance on manually curated dataset")
    def test_clustering(self):
        test_dataset = open('data_test/cluster_data/dataset.tsv', encoding='utf-8')
        reader = csv.reader(test_dataset, delimiter="\t")
        next(reader, None)
        count = 0
        correct = 0
        out_path = 'data_test/cluster_data/dataset_lev.txt'
        out = open(out_path, "w", encoding='utf-8')

        def format_ref(ref):
            year = ref.year if ref.year is not None else "????"
            return "".join(ref.authors) + " " + year + ". " + ref.title + "\n"

        for row in reader:
            if row[1] and row[3]:
                ref1 = Reference(row[1])
                ref2 = Reference(row[3])
                same = ref1.year == ref2.year
                ratio = 0
                if same:
                    ratio = Levenshtein.ratio(ref1.title.lower(), ref2.title.lower())
                    same = ratio >= 0.7
                ground = float(row[5])
                if ground > 0.5 and same or ground < 0.5 and not same:
                    correct += 1.0
                count += 1.0
                out.write(format_ref(ref1))
                out.write(format_ref(ref2))
                res = 1.0 if same else 0.0
                out.write(str(res) + " (" + str(ratio) + ")" + "\n\n")
        success_rate = correct / count
        self.assertGreaterEqual(success_rate, 0.9)
        print(success_rate)
        out.close()
        test_dataset.close()

    # @unittest.skip("Disambiguate selected references")
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
            print(ref)
            parts = re.split('[;,()]', ref)
            title = max(parts, key=len)
            book_data = query_google_books(title, "")
            self.assertGreaterEqual(int(book_data['totalItems']), 1)

    # @unittest.skip("Disambiguate parsed references from file")
    def test_ref_parsing(self):
        data = get_clustered_refs_flat('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
        data = data[:50]
        num_parsing_errors = 0
        count_success = 0
        for text in data:
            ref = Reference(text)
            ref_def = ref.text
            if ref.title:
                author_list = ", ".join(ref.authors)
                ref_def = author_list + '. "' + ref.title + '"'
            num_parsing_errors += 1 if ref.title else 0
            book_data = query_google_books(ref_def)
            if 'items' in book_data:
                for item in book_data["items"]:
                    volume = item["volumeInfo"]
                    volume_def = ""
                    if "authors" in volume.keys():
                        volume_def += ", ".join(volume["authors"]) + ". "
                    if "publishedDate" in volume.keys():
                        volume_def += " " + volume["publishedDate"] + ". "
                    subtitle = " " + volume["subtitle"] if "subtitle" in volume.keys() else ""
                    volume_def += '"' + volume["title"] + subtitle + '"'
                    ratio = Levenshtein.ratio(ref_def.lower(), volume_def.lower())
                    if ratio > 0.5:
                        count_success += 1
                        print("Requested:", ref_def)
                        print("Found:", volume_def, ratio)
        rate_success = 100 * count_success/len(data)
        self.assertGreaterEqual(24, rate_success)
        print("#Successfully disambiguated:", str(rate_success) + "%")
        print("#Parsing errors:", num_parsing_errors)

    # @unittest.skip("Disambiguate references from file via Brill's publication catalogue")
    def test_bib_disambiguation(self):
        import bibtexparser
        from bibtexparser.bparser import BibTexParser
        from bibtexparser.customization import convert_to_unicode
        bibtex_file = open('data_test/Brill_CLS_books.bib', 'r', encoding="utf-8")
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
        bibtex_file.close()
        print("Total publications in the database:", len(bib_database.entries))
        data = get_clustered_refs_flat('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
        found = 0
        out_file = open('data_test/Brill_recognized.txt', "w", encoding='utf-8')
        for text in data:
            ref = Reference(text)
            ratio_max = 0
            best_match = {}
            if ref.title:
                author_list = ", ".join(ref.authors)
                for entry in bib_database.entries:
                    ratio_authors = 0
                    ratio_title = 0
                    if "title" in entry.keys():
                        ratio_title = Levenshtein.ratio(entry["title"], ref.title)
                    if ratio_title >= 0.75:
                        if "author" in entry.keys():
                            ratio_authors = Levenshtein.ratio(entry["author"], author_list)
                        if ratio_title + ratio_authors > ratio_max:
                            ratio_max = ratio_title + ratio_authors
                            best_match = entry
                if ratio_max > 0:
                    found += 1
                    out_file.write(str(ratio_max) + "\n")
                    out_file.write("\t" + author_list + ": " + ref.title + "\n")
                    best_match_authors = best_match["author"] if "author" in best_match else "---"
                    out_file.write("\t" + best_match_authors + ": " + best_match["title"] + "\n")
        print(str(found) + " out of " + str(len(data)))
        out_file.close()

    # @unittest.skip("Query based on keywords + intitle should help to locate requested publication")
    def test_google_api_format(self):
        ref = "The Brazen House. A Study of the Vestibule of the Imperial Palace of Constantinople"
        ext_text = "The Brazen House"
        ext = "&intitle:" + quote(ext_text)
        res = query_google_books(ref, ext)
        self.assertEqual(10, len(res["items"]))
        self.assertEqual("The Brazen House", res["items"][0]["volumeInfo"]["title"])

    # @unittest.skip("Parsing of indices from zipped pdf files")
    def test_extract_and_parse_indices(self):
        from parser_corpus import parse_corpus
        corpus_list = parse_corpus('data', extract_index=True, extract_bib=False, sample_size=500)
        corpus = corpus_list[0]
        for pub in corpus.publications:
            if pub.index_refs:
                for ref in pub.index_refs:
                    print(ref)

    # @unittest.skip("Evaluation of disambiguation on human labelled data")
    def test_evaluate_disambiguation(self):
        with open('data_test/ref_sample_disambiguation_100.csv', "r", encoding='utf-8', newline="") as f:
            reader = csv.reader(f, delimiter=",")
            # Skip header
            next(reader, None)
            count = 0
            google_count = 0
            google_success = 0
            crossref_count = 0
            crossref_success = 0
            for row in reader:
                text = row[0]
                ref = Reference(text)
                # print(ref.authors, ref.title)
                ext = "&intitle:" + quote(ref.title)

                crossref = row[4]
                google = row[5]
                other = row[7]

                if google != 'n/a':
                    google_count += 1
                    res = query_google_books(ref.title, ext)
                    items = res["items"]
                    google_id = items[0]["selfLink"].split('/')[-1]
                    given_google_id = google.split('=')[-1]
                    print("Google API:", google_id, given_google_id)
                    if google_id == given_google_id:
                        google_success += 1

                if crossref != 'n/a':
                    crossref_count += 1
                    res = query_crossref_pub(text)
                    doi = res["DOI"].split('/')[-1]
                    given_doi = crossref.split('/')[-1]
                    print("Crossref API:", doi, given_doi)
                    if given_doi.startswith(doi) or doi.startswith(given_doi):
                        crossref_success += 1

                count += 1
                if count > 100:
                    break
            print(google_success, google_count)
            print(crossref_success, crossref_count)

    # @unittest.skip("Estimation of success rate of disambiguation")
    def test_self_evaluate_disambiguation(self):
        header = ["Reference", "Google API", "CrossRef", "DOI", "ISBN", "Industry identifiers", "Remarks"]
        f = open('data_test/ref_sample_disambiguation_revised.csv', "w", encoding='utf-8', newline="")
        writer = csv.writer(f)
        writer.writerow(header)

        with open('data_test/ref_sample_disambiguation_100.csv', "r", encoding='utf-8', newline="") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader, None)

            count = 0
            google_success = 0
            crossref_success = 0

            for row in reader:
                text = row[0]
                ref = Reference(text)

                disambiguate_google_books(ref)
                if ref.url_google:
                    google_success += 1

                disambiguate_crossref(ref)
                if ref.url_crossref is not None or ref.doi is not None:
                    crossref_success += 1

                if ref.url_google is not None or ref.url_crossref is not None or ref.doi is not None:
                    count += 1

                print(text, ref.url_google, ref.url_crossref, ref.doi, ref.isbn, ref.industry_identifiers)
                # writer.writerow([text, ref.url_google, ref.url_crossref, ref.doi, ref.isbn, ref.industry_identifiers, ""])

            print(count, google_success, crossref_success)

    @unittest.skip("Disambiguation with OpenCitation API")
    def test_query_open_citations(self):
        from disambiguation import query_open_citations
        book_data = query_open_citations("The Brazen House.")
        print(book_data)

    # TODO Disambiguation/Linking of indices
    # Start by trying to look up the surface of index entries in Matteo’s hucitlib (example query: Aeschylus Agamemnon).
    # Given that hucitlib is much more narrowly focussed than Wikidata this may ease the task at the beginning
    # Assess percentage of entries in index locorum that are ambiguous and difficult to link (2+ linking candidates)
    # Keep Wikidata look-up as a fallback for index entries that don’t have a match in hucitlib
    # Before linking, and for the sake of efficiency, an intermediate step could be the clustering of index entries (e.g. “Aeschylus, Agamemnon” in publication A is grouped together with similar entries in other indexes)


if __name__ == '__main__':
    unittest.main()
