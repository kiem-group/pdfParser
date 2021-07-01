from browser import *
from os import listdir
from os.path import isfile, join
import Levenshtein as lev
from model.reference import Reference


def get_refs(my_path):
    bib_files = [f for f in listdir(my_path) if f.endswith('-bibliography.txt') and isfile(join(my_path, f))]
    refs = []
    for filename in bib_files:
        file_path = join(my_path, filename)
        f = open(file_path, mode="r", encoding="utf-8")
        content = f.read()
        file_refs = content.split("\n\n")
        refs.extend(file_refs)
    return refs


def get_cross_ref(refs):
    print("Searching for references:", len(refs))
    from crossref.restful import Works
    works = Works()
    for ref in refs:
        print(ref)
        pub = works.query(bibliographic=ref)
        for item in pub:
            print(item['author'], item['title'])
        print('\n')


def is_ref_found(ref, ref_cluster, threshold=0.75):
    m = len(ref_cluster)
    if m == 0:
        return False
    str1 = ref.lower()
    # sum_ratio = 0
    # for v in ref_cluster:
    #     str2 = v.lower()
    #     if str1 == str2:
    #         sum_ratio += 1.0
    #     else:
    #         sum_ratio += lev.ratio(str1, str2)
    # avg_ratio = sum_ratio / m
    avg_ratio = lev.ratio(str1, ref_cluster[0])
    return avg_ratio >= threshold


def group_by_levenshtein_ratio(refs, ref_clusters, threshold=0.75):
    n = len(refs)
    print("Grouping references:", n)
    for i in range(n):
        ref = refs[i]
        not_found = True
        for ref_cluster in ref_clusters:
            if is_ref_found(ref, ref_cluster, threshold):
                ref_cluster.append(ref)
                not_found = False
                break
        if not_found:
            ref_clusters.append([ref])
        if i % 10 == 0:
            print(i)


if __name__ == '__main__':
    # Find publication and index files
    parse_corpus('data')

    # Compute editing distance for local clustering of similar publications
    # path = 'data/41a8cdce8aae605806c445f28971f623'
    # data = get_refs(path)
    #
    # clusters = [[]]
    # group_by_levenshtein_ratio(data, clusters, 0.75)
    #
    # out_path = join(path, "clusters.txt")
    # out_file = open(out_path, "w", encoding='utf-8')
    # for cluster in clusters:
    #     for entry in cluster:
    #         out_file.write(entry + '\n')
    #     out_file.write('\n\n')
    # out_file.close()

    # Disambiguate data
    # get_cross_ref(data)
