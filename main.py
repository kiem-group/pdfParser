from model.batch import Batch
from model.disambiguate_bibliographic import DisambiguateBibliographic
from model.disambiguate_index import DisambiguateIndex
from model.reference_index import IndexReference
from model.reference_bibliographic import Reference
from model.log_config import config_logger
from os import listdir
from model.db_connector import DBConnector
from os.path import isfile, join
import os
import time
from model.cluster_bibliographic import ClusterSet
from model.cluster_index import IndexClusterSet

if __name__ == '__main__':

    # Parse publication archive and save knowledge graph in a DB
    def populate_db(limit: int = None, batch_size: int = 100):
        # Process publication archives in batches
        zip_arr = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
        for zip in zip_arr:
            logger.info("Started corpus processing!")
            # 1. Parse publication batch
            corpus_zip_path = join(dir_path, zip)
            start_idx = 0
            while limit is None or start_idx < limit:
                # Full version with reference and index mining
                batch = Batch.from_zip(zip_path=corpus_zip_path, start=start_idx, size=batch_size,
                                       extract_bib=True, extract_index=True)
                # Fast version without PDF mining, use it, e.g., to explore catalogue content
                # batch = Batch.from_zip(zip_path=corpus_zip_path, start=start_idx, size=batch_size,
                #                        extract_bib=False, extract_index=False)
                if batch is not None:
                    # 2. Cluster similar references in the corpus
                    # batch.cluster()
                    # 3. Add batch to the knowledge graph
                    db.create_graph(batch)
                    logger.info("Processed and saved the batch!")
                else:
                    logger.info("Finished corpus processing!")
                    break
                start_idx += batch_size
            logger.info("Finished corpus processing!")

    # Disambiguate bibliographic references from the DB
    def disambiguate_bib(unprocessed_only: bool = True, limit: int = None, order=0):
        count_found = 0
        count_links = 0
        refs = db.query_bib_refs(limit, unprocessed_only, order)
        total = len(refs)
        print("Extracted bib references: ", total)
        session = db.driver.session()
        for i, ref in enumerate(refs):
            ref.refers_to = []
            try:
                DisambiguateBibliographic.find_google_books(ref)
            except Exception as e:
                print("Failed to disambiguate via GoogleAPI", e, ref.text)
            try:
                DisambiguateBibliographic.find_crossref(ref)
            except Exception as e:
                print("Failed to disambiguate via Crossref", e, ref.text)
            count_found += 1 if len(ref.refers_to) > 0 else 0
            count_links += len(ref.refers_to)
            for ext_pub in ref.refers_to:
                try:
                    db.create_ext_pub(ext_pub, ref.UUID, session)
                except Exception as e:
                    print("Failed to serialize reference", e)
            # Mark reference as disambiguated, even if the match is not found
            db.set_disambiguated(Reference.__name__, ref.UUID, session)
            print("Processed:" + str(i + 1) + "; disambiguated:" + str(count_found) + "; links:" + str(count_links), ref.UUID)
        # Merge copies with the same uri
        db.merge_ext_pub()
        logger.info("Disambiguated: %d out of %d bibliographic references!", count_found, total)

    # Disambiguate index references from the DB
    def disambiguate_index(unprocessed_only: bool = True, limit: int = None, order=0):
        count_found = 0
        count_links = 0
        refs = db.query_index_refs(limit, unprocessed_only, order)
        total = len(refs)
        print("Extracted index references: ", total)
        session = db.driver.session()
        for i, idx in enumerate(refs):
            DisambiguateIndex.find_wikidata(idx)
            count_found += 1 if len(idx.refers_to) > 0 else 0
            count_links += len(idx.refers_to)
            for ext_idx in idx.refers_to:
                try:
                    db.create_ext_index(ext_idx, idx.UUID, session)
                except Exception as e:
                    print("Failed to serialize index", e)
                # Mark reference as disambiguated, even if the match is not found
            db.set_disambiguated(IndexReference.__name__, idx.UUID, session)
            print("Processed:" + str(i + 1) + "; disambiguated:" + str(count_found) + "; links:" + str(count_links), idx.UUID)
        # Merge copies with the same uri
        # db.merge_ext_idx()
        logger.info("Disambiguated: %d out of %d index references!", count_found, total)

    def find_missing_pubs():
        saved_file_names = db.query_pubs_jats_files()
        print(len(saved_file_names))
        zip_arr = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
        for zip in zip_arr:
            # 1. Parse publication batch
            corpus_zip_path = join(dir_path, zip)
            batch = Batch.from_zip(zip_path=corpus_zip_path, extract_bib=False, extract_index=False)
            all_file_names = [item.jats_file for item in batch.publications]
            print(len(all_file_names))
            missing_file_names = [item for item in all_file_names if item not in saved_file_names]
            print(len(missing_file_names))
            print(missing_file_names)

    def cluster_bib():
        cluster_set_bib = ClusterSet()
        refs = db.query_bib_refs(100)
        for i, ref in enumerate(refs):
            cluster_set_bib.add_references(ref)
            if i % 100 == 0:
                print(i, "Number of bib clusters: %d", cluster_set_bib.num_clusters)

    def cluster_index():
        cluster_set_index = IndexClusterSet(threshold=0.9)
        refs = db.query_index_refs(100)
        for i, ref in enumerate(refs):
            cluster_set_index.add_references(ref)
            if i % 100 == 0:
                print(i, "Number of bib clusters: %d", cluster_set_index.num_clusters)

    # -1. Create logger
    logger = config_logger()
    # 0. Prepare storage
    db_address = os.environ.get('KIEM_NEO4J')
    pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
    db = DBConnector(db_address, "neo4j", pwd)

    # Step 1: extract publications from archive, parse references and indices, cluster, populate the database
    dir_path = "data_all"

    # Use to clean the DB (attention - do not clean KIEM_NEO4J, it takes days to populate!!!)
    # /* db.clear_graph() */

    # populate_db()
    # db.merge_clusters()

    # find_missing_pubs()

    # Step 2: disambiguate a given number of references
    # Step 3: disambiguate a given number of indices
    # db.delete_external_pub()
    # db.delete_external_index()

    start = time.perf_counter()

    disambiguate_bib(True, 2000, -1)
    # disambiguate_index(True, 1000, 1)

    end = time.perf_counter()
    print(f'Finished in {round(end-start, 2)} second(s)')




