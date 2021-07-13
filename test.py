import unittest
import csv
import Levenshtein as lev
import re

class TestClassifier(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        super(TestClassifier, self).setUpClass()

    # Accuracy of reference clustering based on Levenshtein distance on manually curated dataset
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
            ratio = lev.ratio(str1, str2)
            same = ratio > 0.75
            ground = float(row[5])
            if ground > 0.5 and same or ground < 0.5 and not same:
                correct += 1.0
            count += 1.0
            out.write(row[1] + '\n')
            out.write(row[3] + '\n')
            res = 1.0 if same else 0.0
            out.write(str(res) + '\n\n')
        success_rate = correct / count
        self.assertGreaterEqual(success_rate, 0.82)
        out.close()
        test_dataset.close()


    def test_disambiguation(self):
        refs = [
            "Vernant, Jean - Pierre, Mythe et société en Grèce ancienne (Paris, 2004).",
            "Vernant, Jean - Pierre, Problèmes de la guerre en Grèce ancienne (Paris, 1999).",
            "Vernant, Jean-Pierre, “One ... Two ... Three: Eros,” in Before Sexuality: The Construction of Erotic Experience in the Ancient Greek World, ed. Donald M. Halperin, John J. Winkler, and Froma I. Zeitlin (Princeton, 1999), 465-478.",
            "Syme, Ronald, The Roman Revolution (Oxford, 1939).",
            "Syme, R., The Roman Revolution (Oxford, 1960)."
        ]
        # refs = [
        #     "Mythe et société en Grèce ancienne",
        #     "Problèmes de la guerre en Grèce ancienne",
        #     "Before Sexuality: The Construction of Erotic Experience in the Ancient Greek World",
        #     "The Roman Revolution"
        # ]
        import json
        import urllib
        from urllib.request import urlopen
        api = "https://www.googleapis.com/books/v1/volumes?q=intitle:"
        for ref in refs:
            parts = re.split('[;,()]', ref)
            # for part in parts:
            #     print(part)
            title = max(parts, key=len)
            print(title)
            url = api + urllib.parse.quote(title)
            resp = urlopen(url)
            book_data = json.load(resp)
            # self.assertGreaterEqual(int(book_data['totalItems']), 1)
            print(book_data)


if __name__ == '__main__':
    unittest.main()

