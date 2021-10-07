from parser_corpus import parse_corpus
from clustering import cluster_refs, get_clustered_refs, get_clustered_refs_flat
from disambiguation import disambiguate_crossref, disambiguate_google_books
from model.reference import Reference

if __name__ == '__main__':
    # 1. Find publication and index files
    # Input: folder with zipped publication archives (one or more)
    # Output: folders named as zip archives containing a set of files with parsed publications:
    # (Optionally: list of parsed publications - not suitable for large datasets)
    # parse_corpus('data', extract_bib=True, extract_index=True)

    # 2. Cluster similar references in the corpus
    # cluster_refs('data/41a8cdce8aae605806c445f28971f623')

    # 3. Disambiguate references by querying external resources
    # Can be optimized - disambiguate only first entry in each cluster
    data = get_clustered_refs_flat('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
    for ref_text in data:
        ref = Reference(ref_text)
        disambiguate_google_books(ref)
        disambiguate_crossref(ref)
