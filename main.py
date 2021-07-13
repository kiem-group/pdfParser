from parser_corpus import parse_corpus
from clustering import cluster_refs, get_clustered_refs
from disambiguation import query_cross_ref, query_google_books

if __name__ == '__main__':
    # 1. Find publication and index files
    # Input: folder with zipped publication archives (one or more)
    # Output: folders named as zip archives containing a set of files:
    #  i) with references, named [publication-archive-name]-bibliography.txt
    #  ii) with indices, named [publication-archive-name]-[index-type]-[counter].txt
    parse_corpus('data')

    # 2. Cluster similar references in the corpus
    # cluster_refs('data/41a8cdce8aae605806c445f28971f623')

    # 3. Disambiguate references by querying external resources

    # 3a) Query CrossRef
    # query_cross_ref(data)

    # 3b) Query Google books
    # data = get_clustered_refs('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
    # query_google_books(data)
