from parser_corpus import parse_corpus
from clustering import cluster_refs, get_clustered_refs, get_clustered_refs_flat
from disambiguation import disambiguate_crossref, disambiguate_google_books
from model.reference import Reference
from parser_corpus import parse_corpus
from db_connector import DBConnector

if __name__ == '__main__':
    # 1. Find publication and index files
    # Input: folder with zipped publication archives (one or more)
    # Output: folders containing files with parsed publications:
    # (Optionally: list of parsed publications - not suitable for large datasets)
    corpus_list = parse_corpus('data', extract_index=False, extract_bib=True, sample_size=2)
    corpus = corpus_list[0]

    # 2. Cluster similar references in the corpus
    # cluster_refs('data/41a8cdce8aae605806c445f28971f623')

    # 3. Disambiguate references by querying external resources
    # Can be optimized - disambiguate only first entry in each cluster
    # data = get_clustered_refs_flat('data/41a8cdce8aae605806c445f28971f623/clusters.txt')
    for pub in corpus.publications:
        for ref in pub.bib_refs:
            try:
                disambiguate_google_books(ref)
                disambiguate_crossref(ref)
            except:
                print("Failed to disambiguate")
            # if ref.refers_to is not None:
            #     for ext_pub in ref.refers_to:
            #         print(ext_pub.serialize())

    graph = DBConnector("bolt://3.87.203.64:7687", "neo4j", "###")
    graph.create_graph(corpus.publications)
    # Check content
    # graph.query_graph()
    graph.close()
