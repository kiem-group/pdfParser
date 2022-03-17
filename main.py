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

if __name__ == '__main__':

    # Parse publication archive and save knowledge graph in a DB
    def populate_db(limit: int = None, batch_size: int = 20):
        # Process publication archives in batches
        dir_path = "data"
        zip_arr = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
        if len(zip_arr) > 0:
            logger.info("Started corpus processing!")
            # 1. Parse publication batch
            corpus_zip_path = join(dir_path, zip_arr[0])
            start_idx = 0
            while limit is None or start_idx < limit:
                batch = Batch.from_zip(zip_path=corpus_zip_path, start=start_idx, size=batch_size,
                                       extract_bib=True, extract_index=True)
                if batch is not None:
                    # 2. Cluster similar references in the corpus
                    batch.cluster()
                    # 3. Add batch to the knowledge graph
                    db.create_graph(batch)
                    logger.info("Processed and saved the batch!")
                else:
                    logger.info("Finished corpus processing!")
                    break
                start_idx += batch_size
            logger.info("Finished corpus processing!")

    # Disambiguate bibliographic references from the DB
    def disambiguate_bib(unprocessed_only: bool = True, limit: int = 100):
        count_found = 0
        count_links = 0
        refs = db.query_bib_refs(limit, unprocessed_only)
        total = len(refs)
        print("Extracted bib references: ", total)
        session = db.driver.session()
        for i, ref in enumerate(refs):
            ref.refers_to = []
            DisambiguateBibliographic.find_google_books(ref)
            DisambiguateBibliographic.find_crossref(ref)
            count_found += 1 if len(ref.refers_to) > 0 else 0
            count_links += len(ref.refers_to)
            for ext_pub in ref.refers_to:
                db.create_ext_pub(ext_pub, ref.UUID, session)
            # Mark reference as disambiguated, even if the match is not found
            db.set_disambiguated(Reference.__name__, ref.UUID, session)
            print("Processed:" + str(i + 1) + "; disambiguated:" + str(count_found) + "; links:" + str(count_links))
        # Merge copies with the same uri
        db.merge_ext_pub()
        logger.info("Disambiguated: %d out of %d bibliographic references!", count_found, total)

    # Disambiguate index references from the DB
    def disambiguate_index(unprocessed_only: bool = True, limit: int = 100):
        count_found = 0
        count_links = 0
        refs = db.query_index_refs(limit, unprocessed_only)
        total = len(refs)
        print("Extracted index references: ", total)
        session = db.driver.session()
        for i, idx in enumerate(refs):
            DisambiguateIndex.find_wikidata(idx)
            count_found += 1 if len(idx.refers_to) > 0 else 0
            count_links += len(idx.refers_to)
            for ext_idx in idx.refers_to:
                db.create_ext_index(ext_idx, idx.UUID, session)
            # Mark reference as disambiguated, even if the match is not found
            db.set_disambiguated(IndexReference.__name__, idx.UUID, session)
            print("Processed:" + str(i + 1) + "; disambiguated:" + str(count_found) + "; links:" + str(count_links))
        # Merge copies with the same uri
        db.merge_ext_idx()
        logger.info("Disambiguated: %d out of %d index references!", count_found, total)

    # -1. Create logger
    logger = config_logger()
    # 0. Prepare storage
    pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
    db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", pwd)

    # Step 1: extract publications from archive, parse references and indices, cluster, populate the database
    db.clear_graph()
    populate_db()
    db.merge_clusters()

    # Step 2: disambiguate a given number of references
    # db.delete_external_pub()
    # disambiguate_bib(True)

    # Step 3: disambiguate a given number of indices
    # db.delete_external_index()
    # disambiguate_index(True)






