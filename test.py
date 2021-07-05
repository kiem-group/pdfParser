import unittest
import csv
import Levenshtein as lev


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
        for row in reader:
            str1 = row[1].lower()
            str2 = row[3].lower()
            ratio = lev.ratio(str1, str2)
            same = ratio > 0.75
            ground = float(row[5])
            if ground > 0.5 and same or ground < 0.5 and not same:
                correct += 1.0
            count += 1.0
        success_rate = correct / count
        self.assertGreaterEqual(success_rate, 0.82)
        test_dataset.close()


if __name__ == '__main__':
    unittest.main()

