from model.batch import Batch
from os import listdir
from model.db_connector import DBConnector
from os.path import isfile, join

if __name__ == '__main__':
    # Prepare storage
    db = DBConnector("neo4j+s://aeb0fdae.databases.neo4j.io:7687", "neo4j", "GykPhfy9DSj7EbiHJgUeojsWdl6azVEMHhlvNDwhHnY")
    db.clear_graph()

    # Process publication archives in batches
    dir_path = "data"
    start_idx = 1
    # Larger batch is better for clustering as we do not cluster references across batches
    batch_size = 3
    end_idx = 3
    zip_arr = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
    for corpus_zip_name in zip_arr:
        # 1. Parse publication batch
        corpus_zip_path = join(dir_path, corpus_zip_name)
        batch = Batch.from_zip(zip_path=join(dir_path, corpus_zip_name), start=start_idx, size=batch_size)
        # 2. Cluster similar references in the corpus
        batch.cluster()
        # 3. Disambiguate references by querying external resources
        batch.disambiguate()
        # 4. Add batch to the knowledge graph
        db.create_graph(batch)
        # Testing: abort after a couple of batches
        start_idx += batch_size
        if start_idx > end_idx:
            break

    db.close()
