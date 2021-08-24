from os import listdir
from os.path import isfile, join
import zipfile
import os
from model.corpus import Corpus
from model.publication import Publication


def parse_corpus(my_path):
    zip_arr = [f for f in listdir(my_path) if isfile(join(my_path, f))]
    corpus_arr = []
    for corpus_zip_name in zip_arr:
        corpus_arr.append(parse_corpus_zip(join(my_path, corpus_zip_name)))
    return corpus_arr


# Returns corpus object that contains information about all publications
def parse_corpus_zip(corpus_zip_path):
    corpus = Corpus(zip_path=corpus_zip_path, publications=[])
    corpus_zip = zipfile.ZipFile(corpus_zip_path)
    corpus_dir_path = os.path.splitext(corpus_zip_path)[0]
    for pub_zip_name in corpus_zip.namelist():
        pub_dir_name = os.path.splitext(pub_zip_name)[0]
        pub_dir_path = join(corpus_dir_path, pub_dir_name)
        corpus_zip.extract(pub_zip_name, pub_dir_path)
        pub_zip_path = join(pub_dir_path, pub_zip_name)
        corpus.add_publication(Publication(pub_zip_path, extract_bib=True))
        try:
            os.remove(pub_zip_path)
            os.rmdir(pub_dir_path)
        except:
            corpus.other_errors += 1
    return corpus
