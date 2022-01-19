import csv
import unittest
from urllib.parse import quote
import Levenshtein
from model.disambiguate_bibliographic import DisambiguateBibliographic
from model.batch import Batch
from model.reference_bibliographic import Reference


def get_clustered_refs_flat(file_path) -> [str]:
    f = open(file_path, mode="r", encoding="utf-8")
    clusters = f.read().split("\n\n")
    clustered_refs = [ref for ref in clusters if ref]
    f.close()
    return clustered_refs


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
        corpus_list = Batch.from_zip('data/41a8cdce8aae605806c445f28971f623.zip')
        corpus = corpus_list[0]
        valid_refs = []
        for pub in corpus.publications:
            if pub.bib_refs:
                for ref in pub.bib_refs:
                    if ref.authors and ref.year and ref.title:
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
        out.close()
        test_dataset.close()

    # Disambiguate parsed references from file
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
            book_data = DisambiguateBibliographic.query_google_books(ref_def)
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
        print("#Successfully disambiguated:", str(rate_success) + "%")
        print("#Parsing errors:", num_parsing_errors)
        self.assertGreaterEqual(24, rate_success)

    # Disambiguate references from file via Brill's publication catalogue
    def test_bib_disambiguation(self):
        import bibtexparser
        from bibtexparser.bparser import BibTexParser
        from bibtexparser.customization import convert_to_unicode
        bibtex_file = open('data_test/Brill_CLS_books.bib', 'r', encoding="utf-8")
        parser = BibTexParser()
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
        bibtex_file.close()
        print("Total publications in the database:", len(bib_database.refs))
        data = get_clustered_refs_flat('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
        found = 0
        out_file = open('data_test/Brill_recognized.txt', "w", encoding='utf-8')
        for text in data:
            ref = Reference(text)
            ratio_max = 0
            best_match = {}
            if ref.title:
                author_list = ", ".join(ref.authors)
                for entry in bib_database.refs:
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


if __name__ == '__main__':
    unittest.main()
