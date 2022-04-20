import csv
import unittest
import Levenshtein
from model.reference_bibliographic import Reference


class TestClassifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestClassifier, cls).setUpClass()

    # Accuracy of reference clustering based on Levenshtein distance on manually curated dataset
    def test_clustering(self):
        test_dataset = open('data_test/cluster_data/dataset.tsv', encoding='utf-8')
        reader = csv.reader(test_dataset, delimiter="\t")
        next(reader, None)
        count = 0
        correct = 0
        out_path = 'data_test/cluster_data/dataset_lev.txt'
        out = open(out_path, "w", encoding='utf-8')
        threshold = 1

        def format_ref(ref):
            year = ref.year if ref.year is not None else "????"
            return ref.author + " " + year + ". " + ref.title + "\n"

        for row in reader:
            if row[1] and row[3]:
                ref1 = Reference(row[1])
                ref2 = Reference(row[3])
                same = ref1.year == ref2.year
                ratio = 0
                if same:
                    m = min(len(ref1.title), len(ref2.title))
                    t1 = ref1.title.lower()[0:m]
                    t2 = ref2.title.lower()[0:m]
                    ratio = Levenshtein.ratio(t1, t2)
                same = ratio >= threshold
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
        print(threshold, correct, count, success_rate)
        out.close()
        test_dataset.close()


if __name__ == '__main__':
    unittest.main()
