import unittest
import csv
import Levenshtein as lev
import re
from clustering import get_clustered_refs_flat
from model.reference import Reference
import Levenshtein as lev


class TestClassifier(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestClassifier, cls).setUpClass()

    # Accuracy of reference clustering based on Levenshtein distance on manually curated dataset
    @classmethod
    @unittest.skip("Skipping clustering accuracy test")
    def test_clustering(cls):
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
                ratio = lev.ratio(str1, str2)
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
        cls.assertGreaterEqual(success_rate, 0.82)
        print(success_rate)
        out.close()
        test_dataset.close()

    @classmethod
    @unittest.skip("Skipping disambiguation test")
    def test_disambiguation(cls):
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
        import urllib
        from urllib.request import urlopen
        api = "https://www.googleapis.com/books/v1/volumes?q=intitle:"
        for ref in refs:
            parts = re.split('[;,()]', ref)
            title = max(parts, key=len)
            print(title)
            url = api + urllib.parse.quote(title)
            resp = urlopen(url)
            book_data = json.load(resp)
            cls.assertGreaterEqual(int(book_data['totalItems']), 1)
            # print(book_data)

    @classmethod
    @unittest.skip("Experimental test with disambiguation of parsed references")
    def test_ref_parsing(cls):
        data = get_clustered_refs_flat('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
        data = data[:50]
        num_parsing_errors = 0
        import json
        import urllib
        from urllib.request import urlopen
        api = "https://www.googleapis.com/books/v1/volumes?q="
        for text in data:
            # On construction we extract author list, year of publication and title
            ref = Reference(text)
            # print("Reference:", ref)

            url = api + urllib.parse.quote(ref.text)
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
                    ratio = lev.ratio(ref_def.lower(), volume_def.lower())
                    if ratio > 0.5:
                        print(ref_def)
                        print("Found:", volume_def, ratio)
            print()
        print("# FAILS:", num_parsing_errors)
        print(len(data))

    @classmethod
    # @unittest.skip("Disambiguation via Brill's publication catalogue")
    def test_bib_disambiguation(cls):
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
                author_list = "and ".join(ref.authors)
                for entry in bib_database.entries:
                    ratio_authors = 0
                    ratio_title = 0
                    if "title" in entry.keys():
                        ratio_title = lev.ratio(entry["title"], ref.title)
                    if ratio_title >= 0.75:
                        if "author" in entry.keys():
                            ratio_authors = lev.ratio(entry["author"], author_list)
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


if __name__ == '__main__':
    unittest.main()

