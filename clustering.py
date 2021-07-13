from os import listdir
from os.path import isfile, join
import Levenshtein as lev


# Reads references from parsed text file
def get_refs(path):
    bib_files = [f for f in listdir(path) if f.endswith('-bibliography.txt') and isfile(join(path, f))]
    refs = []
    for filename in bib_files:
        file_path = join(path, filename)
        f = open(file_path, mode="r", encoding="utf-8")
        content = f.read()
        file_refs = content.split("\n\n")
        refs.extend(file_refs)
    return refs


# checks if similar references already exists in clusters by matching with first sample in a cluster
def is_ref_found(ref, ref_cluster, threshold=0.75):
    m = len(ref_cluster)
    if m == 0:
        return False
    str1 = ref.lower()
    avg_ratio = lev.ratio(str1, ref_cluster[0])
    return avg_ratio >= threshold


# checks if similar reference already exists in clusters by matching with all samples in a cluster
def is_ref_found_avg(ref, ref_cluster, threshold=0.75):
    m = len(ref_cluster)
    if m == 0:
        return False
    str1 = ref.lower()
    sum_ratio = 0
    for v in ref_cluster:
        str2 = v.lower()
        if str1 == str2:
            sum_ratio += 1.0
        else:
            sum_ratio += lev.ratio(str1, str2)
    avg_ratio = sum_ratio / m
    return avg_ratio >= threshold


# Compute editing distance for local clustering of similar references
def group_by_levenshtein_ratio(refs, ref_clusters, threshold=0.75):
    n = len(refs)
    print("Clustering references:", n)
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
            print("Clustering progress - processed:", i)


def get_clustered_refs(file_path):
    f = open(file_path, mode="r", encoding="utf-8")
    clusters = f.read().split("\n\n")
    clustered_refs = []
    for cluster in clusters:
        clustered_refs.append(cluster.split('\n'))
    return clustered_refs


# Cluster extracted references and export to a file
def cluster_refs(path):
    data = get_refs(path)
    clusters = [[]]
    group_by_levenshtein_ratio(data, clusters, 0.75)
    out_path = join(path, "clusters.txt")
    out_file = open(out_path, "w", encoding='utf-8')
    for cluster in clusters:
        for entry in cluster:
            out_file.write(entry + '\n')
        out_file.write('\n\n')
    out_file.close()
