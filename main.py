from model.batch import Batch
from model.disambiguate_bibliographic import DisambiguateBibliographic
from model.log_config import config_logger
from os import listdir
from model.db_connector import DBConnector
from os.path import isfile, join
import os

if __name__ == '__main__':
    def populate_db(db, logger):
        db.clear_graph()
        # Process publication archives in batches
        dir_path = "data"
        zip_arr = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
        if len(zip_arr) > 0:
            # 1. Parse publication batch
            corpus_zip_path = join(dir_path, zip_arr[0])
            start_idx = 0
            # Larger batch is better for clustering as we do not cluster references across batches
            batch_size = 10
            end_idx = 90
            while start_idx < end_idx:
                batch = Batch.from_zip(zip_path=corpus_zip_path, start=start_idx, size=batch_size,
                                       extract_bib=True, extract_index=True)
                logger.info("Started batch: %d - %d", start_idx, start_idx + batch_size)
                # 2. Cluster similar references in the corpus
                batch.cluster()
                # 3. Add batch to the knowledge graph
                db.create_graph(batch)
                start_idx += batch_size
                logger.info("Finished batch!")

    def disambiguate_existing(db, logger):
        count = 0
        # TODO delete external publication contributors
        # db.detach_delete_nodes("ExternalPublication")
        refs = db.query_bib_refs(100)
        total = len(refs)
        for ref in refs:
            ref.refers_to = []
            DisambiguateBibliographic.find_google_books(ref)
            DisambiguateBibliographic.find_crossref(ref)
            count += len(ref.refers_to)
            for ext_pub in ref.refers_to:
                db.create_ext_pub(ext_pub, ref.UUID)
        logger.info("Disambiguated: %d out of %d bibliographic references!", count, total)

    # -1. Create logger
    logger = config_logger()

    # 0. Prepare storage
    pwd = os.environ.get('KIEM_NEO4J_PASSWORD')
    db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", pwd)
    # populate_db(db, logger)
    disambiguate_existing(db, logger)


