import csv
import unittest
import Levenshtein
from model.batch import Batch
from model.reference_bibliographic import Reference
from model.disambiguate_bibliographic import DisambiguateBibliographic


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

    # Revised disambiguation via analysis of all Google API results
    def test_improved_disambiguation(self):
        test_dataset = open('data_test/test_evaluate_disambiguation_annotated.tsv', encoding='utf-8')
        reader = csv.reader(test_dataset, delimiter="\t")
        header = next(reader, None)
        out_path = 'data_test/test_evaluate_disambiguation_annotated_revised.csv'
        writer = csv.writer(open(out_path, "w", encoding='utf-8', newline=""))
        header.append("GoogleAPI_new")
        writer.writerow(header)
        delta = 0
        for row in reader:
            url_google = []
            if row[0] and ("1" not in row[3]) and ("doi" in row[4]):
                ref = Reference(row[0])
                DisambiguateBibliographic.find_google_books(ref, 0.6)
                if ref.refers_to is not None:
                    url_google = [e.url for e in ref.refers_to if e.url is not None and e.type == "google"]
            out_google = ", ".join(url_google)
            if len(out_google) > 0:
                if row[1] != out_google:
                    delta += 1
            row.append(out_google)
            writer.writerow(row)
        print(delta)

    def test_analyze_disambiguation(self):
        test_dataset = open('data_test/test_evaluate_disambiguation_annotated_revised.tsv', encoding='utf-8')
        reader = csv.reader(test_dataset, delimiter="\t")
        count_filled = 0
        count_filled_human = 0
        count_good = 0
        for row in reader:
            found = True if row[1] or row[2] or row[5] else False
            if found:
                count_filled += 1
            if (not found) and row[3] == "0" and ("https" in row[4]):
                count_filled_human += 1
            if row[3] == "1":
                count_good += 1
            if row[3] == "0.5":
                count_good += 0.5
        print(count_good, count_filled)
        print(count_good, count_filled + count_filled_human)

    # Revised disambiguation via analysis of all Google API results
    def test_analyze_index_disambiguation(self):
        test_dataset = open('data_test/test_evaluate_idx_disambiguation_labels_annotated.tsv', encoding='utf-8')
        reader = csv.reader(test_dataset, delimiter="\t")
        count_filled = 0
        count_filled_human = 0
        count_good = 0
        for row in reader:
            if row[2]:
                count_filled += 1
            if row[3] == "0" and ("https" in row[4]):
                count_filled_human += 1
            if row[3] == "1":
                count_good += 1
            if row[3] == "0.5":
                count_good += 0.5
        print(count_good, count_filled)
        print(count_good, count_filled + count_filled_human)


if __name__ == '__main__':
    unittest.main()
