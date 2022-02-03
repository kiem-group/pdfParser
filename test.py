import csv
import unittest
import Levenshtein
from model.batch import Batch
from model.reference_bibliographic import Reference


class TestClassifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestClassifier, cls).setUpClass()

    @unittest.skip("Random selection of references from zipped pdf files for evaluation of disambiguation")
    def test_random_pick(self):
        import random
        corpus_list = Batch.from_zip('data/41a8cdce8aae605806c445f28971f623.zip')
        corpus = corpus_list[0]
        valid_refs = []
        for pub in corpus.publications:
            if pub.bib_refs:
                for ref in pub.bib_refs:
                    if ref.author and ref.year and ref.title:
                        valid_refs.append(ref)
        samples = random.sample(valid_refs, 500)
        header = ["Reference", "Cited_by_doi", "Cited_by_zip", "Cited_num", "CrossRef", "GoogleAPI", "Brill", "Other",
                  "Remarks"]
        with open('data_test/ref_sample_disambiguation_eval_new.csv', "w", encoding='utf-8', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for sample in samples:
                writer.writerow([sample.text.strip(), sample.cited_by_doi, sample.cited_by_zip, sample.ref_num])

    # Accuracy of reference clustering based on Levenshtein distance on manually curated dataset
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
            return ref.author + " " + year + ". " + ref.title + "\n"

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
        out.close()
        test_dataset.close()


if __name__ == '__main__':
    unittest.main()
