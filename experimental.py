import numpy as np
from os.path import join
from sklearn.cluster import AffinityPropagation
import distance
import csv
import Levenshtein as lev


def print_clustering_ground():
    test_dataset = open('data_test/cluster_data/dataset.tsv', encoding='utf-8')
    reader = csv.reader(test_dataset, delimiter="\t")
    out_path = 'data_test/cluster_data/dataset_ground.txt'
    out = open(out_path, "w", encoding='utf-8')
    next(reader, None)
    for row in reader:
        out.write(row[1] + "\n")
        out.write(row[3] + "\n")
        out.write(row[5] + "\n\n")
    out.close()
    test_dataset.close()


def print_clustering_lev():
    test_dataset = open('data_test/cluster_data/dataset.tsv', encoding='utf-8')
    reader = csv.reader(test_dataset, delimiter="\t")
    next(reader, None)
    out_path = 'data_test/cluster_data/dataset_lev.txt'
    out = open(out_path, "w", encoding='utf-8')
    for row in reader:
        str1 = row[1].lower()
        str2 = row[3].lower()
        ratio = lev.ratio(str1, str2)
        same = ratio > 0.75
        out.write(row[1] + "\n")
        out.write(row[3] + "\n")
        res = 1.0 if same else 0.0
        out.write(str(res) + "\n\n")
    out.close()
    test_dataset.close()


# Affinity-propagation clustering
# We learn the predefined number of clusters, then predict which cluster the new entries fall into,
# but we just need to group same reference occurrences!
def cluster(data, path):
    data = [
        "Vernant, Jean - Pierre, Mythe et sociÃ©tÃ© en GrÃ¨ce ancienne(Paris, ï™„ï™Œï™Šï™‡).",
        "Vernant, Jean - Pierre, ProblÃ¨mes de la guerre en GrÃ¨ce ancienne(Paris, ï™„ï™Œï™‰ï™‹).",
        "Vernant, Jean-Pierre, â€œOne ... Two ... Three: Eros,â€ in Before Sexuality: The Construction of Erotic Experience in the Ancient Greek World, ed. Donald M. Halperin, John J. Winkler, and Froma I. Zeitlin (Princeton, ï™„ï™Œï™Œï™ƒ), ï™‡ï™‰ï™ˆâ€“ï™‡ï™Šï™‹.",
        "Syme, Ronald, The Roman Revolution(Oxford, ï™„ï™Œï™‰ï™ƒ).",
        "Syme, R., The Roman Revolution(Oxford, 1960)."
    ]

    out_path = join(path, "clusters.txt")
    out_file = open(out_path, "w", encoding='utf-8')

    print(len(data))
    data = np.asarray(data)
    lev_similarity = -1 * np.array([[distance.levenshtein(w1, w2) for w1 in data] for w2 in data])
    aff_prop = AffinityPropagation(affinity="precomputed", damping=0.9)
    aff_prop.fit(lev_similarity)
    for cluster_id in np.unique(aff_prop.labels_):
        exemplar = data[aff_prop.cluster_centers_indices_[cluster_id]]
        cluster = np.unique(data[np.nonzero(aff_prop.labels_ == cluster_id)])
        cluster_str = "\n\t".join(cluster)
        out_file.write(" - *%s:* %s" % (exemplar, cluster_str) + "\n\n")
    out_file.close()


# from io import StringIO
# from pdfminer.converter import TextConverter
# from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
# from pdfminer.pdfpage import PDFPage

# from gensim.models import Word2Vec
# from nltk.tokenize import wordpunct_tokenize
# for text in data:
#     words = wordpunct_tokenize(text)
#     for word in words:
#         print(word)
# model = Word2Vec(sentences=data, vector_size=100, window=5, min_count=1, workers=4)
# model.save("word2vec.model")
# ref1 = data[0]
# ref1_clones = model.wv.most_similar(positive=ref1, topn=1)


# def parse_target(in_file, out_path, stats):
#     output_string = StringIO()
#     parser = PDFParser(in_file)
#     doc = PDFDocument(parser)
#     rsrc_mgr = PDFResourceManager()
#     device = TextConverter(rsrc_mgr, output_string, laparams=LAParams())
#     interpreter = PDFPageInterpreter(rsrc_mgr, device)
#     for page in PDFPage.create_pages(doc):
#         interpreter.process_page(page)
#     output = output_string.getvalue()
#     lines = output.splitlines()
#     non_empty_lines = [line for line in lines if line.strip() != ""]
#     out_file = open(out_path, "w")
#     try:
#         for line in non_empty_lines:
#             out_file.write(line+"\n\n")
#     except IOError:
#         # print("Output error", sys.exc_info()[0])
#         stats["output_errors"] += 1
#     in_file.close()
#     out_file.close()

# if any(word in title for word in ['index', 'bibliography']):
#     href = book_part.xpath('.//self-uri/@xlink:href',
#                            namespaces={"xlink": "http://www.w3.org/1999/xlink"})[0]
#     target_pdf = pub_zip.open(href)
#     # Modify output_txt_path to put target files of the same type to a dedicated folder
#     if 'index' in title:
#         corpus.index_count += 1
#         pub.index_files.append(href)
#         # curr_index_types = get_index_types(title)
#         # for type_name in curr_index_types:
#         #     index_types[type_name] = index_types.get(type_name, 0) + 1
#         # ext = "-" + str(len(pub.index_files)) + "_" + ('-'.join(curr_index_types))
#         # output_txt_path = pub_dir_path + ext + ".txt"
#     else:
#         # if 'bibliography' in title:
#         corpus.bibliography_count += 1
#         pub.bib_file = href
#         output_txt_path = pub_dir_path + "-bibliography.txt"
#         parse_target_indent(target_pdf, output_txt_path, bib_config)

# Extract a single file from zip
# pub_zip.extract(file_name, join(corpus_dir_path, 'temp_xml'))

# for type_name in curr_index_types:
#     index_types[type_name] = index_types.get(type_name, 0) + 1
