import unittest
import csv
import re
from clustering import get_clustered_refs_flat
import Levenshtein
from model.publication import Publication
from model.reference import Reference
from model.corpus import Corpus
import json


class TestClassifier(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestClassifier, cls).setUpClass()

    @unittest.skip("Accuracy of reference clustering based on Levenshtein distance on manually curated dataset")
    def test_clustering(self):
        test_dataset = open('data_test/cluster_data/dataset.tsv', encoding='utf-8')
        reader = csv.reader(test_dataset, delimiter="\t")
        # Skip header
        next(reader, None)
        count = 0
        correct = 0
        out_path = 'data_test/cluster_data/dataset_lev.txt'
        out = open(out_path, "w", encoding='utf-8')
        for row in reader:
            str1 = row[1].lower()
            str2 = row[3].lower()
            year1 = 0
            year2 = 0
            try:
                year1 = re.search(r"(\d{4})", str1).group(1)
            except AttributeError:
                print("YEAR NOT FOUND:", str1)
            try:
                year2 = re.search(r"(\d{4})", str2).group(1)
            except AttributeError:
                print("YEAR NOT FOUND:", str2)
            same = year1 == year2
            if same:
                ratio = Levenshtein.ratio(str1, str2)
                same = ratio > 0.75
            ground = float(row[5])
            if ground > 0.5 and same or ground < 0.5 and not same:
                correct += 1.0
            count += 1.0
            out.write(row[1] + "\n")
            out.write(row[3] + "\n")
            res = 1.0 if same else 0.0
            out.write(str(res) + "\n\n")
        success_rate = correct / count
        self.assertGreaterEqual(success_rate, 0.82)
        print(success_rate)
        out.close()
        test_dataset.close()

    @unittest.skip("Disambiguate selected references")
    def test_disambiguation(self):
        refs = [
            "Vernant, Jean - Pierre, Mythe et société en Grèce ancienne (Paris, 2004).",
            "Vernant, Jean - Pierre, Problèmes de la guerre en Grèce ancienne (Paris, 1999).",
            ("Vernant, Jean-Pierre, “One ... Two ... Three: Eros,” in Before Sexuality: ",
                "The Construction of Erotic Experience in the Ancient Greek World, ",
                "ed. Donald M. Halperin, John J. Winkler, and Froma I. Zeitlin (Princeton, 1999), 465-478."),
            "Syme, Ronald, The Roman Revolution (Oxford, 1939).",
            "Syme, R., The Roman Revolution (Oxford, 1960)."
        ]
        import json
        from urllib.request import urlopen
        from urllib.parse import quote
        api = "https://www.googleapis.com/books/v1/volumes?q=intitle:"
        for ref in refs:
            parts = re.split('[;,()]', ref)
            title = max(parts, key=len)
            print(title)
            url = api + quote(title)
            resp = urlopen(url)
            book_data = json.load(resp)
            self.assertGreaterEqual(int(book_data['totalItems']), 1)
            # print(book_data)

    @unittest.skip("Disambiguate parsed references from file")
    def test_ref_parsing(self):
        data = get_clustered_refs_flat('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
        data = data[:50]
        num_parsing_errors = 0
        import json
        from urllib.request import urlopen
        from urllib.parse import quote
        api = "https://www.googleapis.com/books/v1/volumes?q="
        for text in data:
            # On construction we extract author list, year of publication and title
            ref = Reference(text)
            # print("Reference:", ref)
            url = api + quote(ref.text)
            ref_def = ""
            if ref.title:
                author_list = ", ".join(ref.authors)
                ref_def = author_list + '. "' + ref.title + '"'
                # url += "+intitle:" + urllib.parse.quote(ref.title)
                # url += "+inauthor:" + urllib.parse.quote(author_list)
            num_parsing_errors += 1 if ref.title else 0
            # print(url)
            resp = urlopen(url)
            book_data = json.load(resp)
            # cls.assertGreaterEqual(int(book_data['totalItems']), 1)
            # print(book_data)
            if int(book_data['totalItems']) > 0:
                # print(ref.year, "###", ref.authors, "###", ref.title)
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
                        print(ref_def)
                        print("Found:", volume_def, ratio)
            print()
        print("# FAILS:", num_parsing_errors)
        print(len(data))

    @unittest.skip("Disambiguate references from file via Brill's publication catalogue")
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
        # word_pattern = "[\w']+"
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
                        # Do not match titles if their length differs too much
                        # str1 = regexp_tokenize(entry["title"], word_pattern)
                        # str2 = regexp_tokenize(ref.title, word_pattern)
                        # if abs(len(str1) - len(str2)) < 5:
                        ratio_title = Levenshtein.ratio(entry["title"], ref.title)
                    if ratio_title >= 0.75:
                        if "author" in entry.keys():
                            # Do not match authors if their length differs too much
                            # str1 = regexp_tokenize(entry["author"], word_pattern)
                            # str2 = regexp_tokenize(author_list, word_pattern)
                            # if abs(len(str1) - len(str2)) < 5:
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
        header = ["Reference", "Cited_by_doi", "Cited_by_zip", "Cited_num", "CrossRef", "GoogleAPI", "Brill", "Other", "Remarks"]
        with open('data_test/ref_sample_disambiguation_eval_new.csv', "w", encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for sample in samples:
                writer.writerow([sample.text.strip(), sample.cited_by_doi, sample.cited_by_zip, sample.ref_num])

    # @unittest.skip("Query based on keywords + intitle should help to locate requested publication")
    def test_google_api_format(self):
        from disambiguation import query_google_book
        from urllib.parse import quote
        ref = "The Brazen House. A Study of the Vestibule of the Imperial Palace of Constantinople"
        ext_text = "The Brazen House"
        ext = "&intitle:" + quote(ext_text)
        res = query_google_book(ref, ext)
        print(res.items)
        # for book in res.items:
        #     print(book)

    # @unittest.skip("Parsing of indices from zipped pdf files")
    def test_extract_and_parse_indices(self):
        from parser_corpus import parse_corpus
        corpus_list = parse_corpus('data', extract_index=True, extract_bib=False, sample_size=500)
        corpus = corpus_list[0]
        for pub in corpus.publications:
            if pub.index_refs:
                for ref in pub.index_refs:
                    print(ref)


    # @unittest.skip("Evaluation of disambiguation")
    def test_evaluate_disambiguation(self):
        with open('data_test/ref_sample_disambiguation_100.csv', "r", encoding='utf-8', newline="") as f:
            from disambiguation import query_google_book, query_crossref_pub
            from urllib.parse import quote
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
                    res = query_google_book(ref.title, ext)
                    items = res["items"]
                    google_id = items[0]["selfLink"].split('/')[-1]
                    given_google_id = google.split('=')[-1]
                    print("Google API:", google_id, given_google_id)
                    if google_id == given_google_id:
                        google_success += 1

                if crossref != 'n/a':
                    crossref_count += 1
                    res = query_crossref_pub(text)
                    # print(res["DOI"], res["title"])
                    # print(crossref)
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

    def test_self_evaluate_disambiguation(self):
        header = ["Reference", "Google API", "CrossRef", "DOI", "ISBN", "Industry identifiers", "Remarks"]
        f = open('data_test/ref_sample_disambiguation_revised.csv', "w", encoding='utf-8', newline="")
        writer = csv.writer(f)
        writer.writerow(header)

        with open('data_test/ref_sample_disambiguation_100.csv', "r", encoding='utf-8', newline="") as f:
            from disambiguation import query_google_book, query_crossref_pub
            from urllib.parse import quote
            reader = csv.reader(f, delimiter=",")
            # Skip header
            next(reader, None)
            count = 0
            google_success = 0
            crossref_success = 0
            for row in reader:
                new_google = ""
                new_crossref = ""
                new_identifiers = ""
                new_doi = ""
                new_isbn = ""

                text = row[0]
                other = row[7]
                if other != 'n/a':
                    print(other)
                ref = Reference(text)
                # print(ref.authors, ref.title)
                ext = "&intitle:" + quote(ref.title)

                res = query_google_book(ref.title, ext)
                if "items" in res:
                    items = res["items"]
                    if len(items) > 0:
                        if "volumeInfo" in items[0]:
                            google_title = items[0]["volumeInfo"]["title"]
                            ratio = Levenshtein.ratio(ref.title, google_title)
                            # print("Google title:", google_title, ratio)
                            if ratio > 0.75:
                                if "selfLink" in items[0]:
                                    new_google = items[0]["selfLink"]
                                google_success += 1
                                if "industryIdentifiers" in items[0]["volumeInfo"]:
                                    new_identifiers = json.dumps(items[0]["volumeInfo"]["industryIdentifiers"])
                res = query_crossref_pub(text)
                if "title" in res:
                    crossref_title = res["title"]
                    if len(crossref_title) > 0:
                        ratio = Levenshtein.ratio(ref.title, crossref_title[0])
                        # print("Crossref title:", crossref_title[0], ratio)
                        if ratio > 0.75:
                            crossref_success += 1
                            # print(res)
                            if "DOI" in res:
                                new_doi = res["DOI"]
                            if "ISBN" in res:
                                new_isbn = res["ISBN"]
                            if "URL" in res:
                                new_crossref = res["URL"]
                if new_google != "" or new_crossref != "":
                    count += 1
                # print(google_success, count)
                # print(crossref_success, count)
                # print(text, new_google, new_crossref, new_identifiers, new_doi, new_isbn)
                # writer.writerow([text, new_google, new_crossref, new_doi, new_isbn, new_identifiers, ""])
                print(count)

if __name__ == '__main__':
    unittest.main()
