from neo4j import GraphDatabase
from model.publication import Publication
from model.reference_bibliographic import Reference
from model.reference_index import IndexReference


class DBConnector:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clear_graph(self):
        # CQL to clear graph
        cql_delete_relationships = "MATCH (a) -[r] -> () DELETE a, r"
        cql_delete_nodes = "MATCH (a) DELETE a"
        with self.driver.session() as session:
            # Clear graph
            session.run(cql_delete_relationships)
            session.run(cql_delete_nodes)

    # Create

    # Create publication nodes with relationships
    def create_pub(self, pub, session=None):
        if session is None:
            session = self.driver.session()
        # TODO create or update
        # Create publication
        cql_create_pub = """CREATE (:Publication {0})"""
        session.run(cql_create_pub.format(pub.serialize()))
        # Create industry identifiers
        cql_create_id = """CREATE (:Identifier {0})"""
        cql_create_pub_has_identifier = """MATCH (a:Publication), (b:Identifier)
           WHERE a.UUID = $pub_uuid AND b.UUID = $id_uuid CREATE (a)-[:HasIdentifier]->(b)"""
        for industry_id in pub.identifiers:
            session.run(cql_create_id.format(industry_id.serialize()))
            session.run(cql_create_pub_has_identifier, pub_uuid=pub.UUID, id_uuid=industry_id.UUID)
        # Create contributors: editors or authors
        cql_create_contributor = """CREATE (:Contributor {0})"""
        cql_create_pub_has_contributor = """MATCH (a:Publication), (b:Contributor)
                  WHERE a.UUID = $pub_uuid AND b.UUID = $c_uuid CREATE (a)-[:HasContributor {num: $num}]->(b)"""
        # Create editors
        for idx, editor in enumerate(pub.editors):
            session.run(cql_create_contributor.format(editor.serialize()))
            session.run(cql_create_pub_has_contributor, pub_uuid=pub.UUID, c_uuid=editor.UUID, num=idx)
        # Create authors
        for idx, author in enumerate(pub.authors):
            session.run(cql_create_contributor.format(author.serialize()))
            session.run(cql_create_pub_has_contributor, pub_uuid=pub.UUID, c_uuid=author.UUID, num=idx)
        # Create bibliographic references
        self.create_bib_refs(pub, session)
        # Create index references
        self.create_index_refs(pub, session)

    # Create bibliographic references
    def create_bib_refs(self, pub, session=None):
        if session is None:
            session = self.driver.session()
        # CQL to create reference nodes
        cql_create_ref = """CREATE (:Reference {0})"""
        cql_create_pub_cites_ref = """MATCH (a:Publication), (b:Reference)
           WHERE a.UUID = $pub_uuid AND b.UUID = $ref_uuid CREATE (a)-[:Cites]->(b)"""
        for ref in pub.bib_refs:
            session.run(cql_create_ref.format(ref.serialize()))
            session.run(cql_create_pub_cites_ref, pub_uuid=pub.UUID, ref_uuid=ref.UUID)
            if ref.refers_to is not None:
                for ext_pub in ref.refers_to:
                    self.create_ext_pub(ext_pub, ref.UUID, session)

    # Create index references
    def create_index_refs(self, pub, session=None):
        if session is None:
            session = self.driver.session()
        # CQL to create reference nodes
        cql_create_idx = """CREATE (:IndexReference {0})"""
        cql_create_pub_includes_idx = """MATCH (a:Publication), (b:IndexReference)
           WHERE a.UUID = $pub_uuid AND b.UUID = $ref_uuid CREATE (a)-[:Includes]->(b)"""
        for idx in pub.index_refs:
            session.run(cql_create_idx.format(idx.serialize()))
            session.run(cql_create_pub_includes_idx, pub_uuid=pub.UUID, ref_uuid=idx.UUID)
            # if ref.refers_to is not None:
            #     for ext_pub in ref.refers_to:
            #         self.create_ext_pub(ext_pub, ref.UUID, session)

    # Create external publications that disambiguate references
    def create_ext_pub(self, ext_pub, ref_uuid, session=None):
        if session is None:
            session = self.driver.session()
        # CQL to create external publications
        cql_create_ext_pub = """CREATE (b:ExternalPublication {0})"""
        cql_create_ref_refers_to_ext_pub = """MATCH (a:Reference), (b:ExternalPublication)
           WHERE a.UUID = $ref_uuid AND b.UUID = $ext_pub_uuid CREATE (a)-[:RefersTo]->(b)"""
        session.run(cql_create_ext_pub.format(ext_pub.serialize()))
        session.run(cql_create_ref_refers_to_ext_pub, ref_uuid=ref_uuid, ext_pub_uuid=ext_pub.UUID)

    # Create clusters of related references
    def create_cluster(self, cluster, session=None):
        if session is None:
            session = self.driver.session()
        # Save only meaningful clusters
        if len(cluster.refs) > 1:
            cql_create_cluster = """CREATE (b:Cluster {0})"""
            session.run(cql_create_cluster.format(cluster.serialize()))
            for ref in cluster.refs:
                cql_create_ref_belongs_to_cluster = """MATCH (a:Reference), (b:Cluster)
                   WHERE a.UUID = $ref_uuid AND b.UUID = $cluster_uuid CREATE (a)-[:BelongsTo]->(b)"""
                session.run(cql_create_ref_belongs_to_cluster, ref_uuid=ref.UUID, cluster_uuid=cluster.UUID)

    def create_index_cluster(self, cluster, session=None):
        if session is None:
            session = self.driver.session()
        # Save only meaningful clusters
        if len(cluster.refs) > 1:
            cql_create_cluster = """CREATE (b:IndexCluster {0})"""
            session.run(cql_create_cluster.format(cluster.serialize()))
            for ref in cluster.refs:
                cql_create_ref_belongs_to_cluster = """MATCH (a:IndexReference), (b:IndexCluster)
                   WHERE a.UUID = $ref_uuid AND b.UUID = $cluster_uuid CREATE (a)-[:BelongsTo]->(b)"""
                session.run(cql_create_ref_belongs_to_cluster, ref_uuid=ref.UUID, cluster_uuid=cluster.UUID)

    # Create knowledge graph
    def create_graph(self, batch):
        with self.driver.session() as session:
            # Create publications
            if batch.publications:
                for pub in batch.publications:
                    try:
                        self.create_pub(pub, session)
                    except:
                        print("Failed to serialize publication: ", pub.UUID)
            if batch.cluster_set_bib and batch.cluster_set_bib.clusters:
                for cluster in batch.cluster_set_bib.clusters:
                    self.create_cluster(cluster, session)

    # Query

    # Retrieve all publications
    def query_pubs(self, limit=None):
        pubs = []
        cql_pubs = "MATCH (a:Publication) return a"
        if limit is not None:
            cql_pubs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_pubs)
            db_pubs = [record for record in nodes.data()]
            for db_pub in db_pubs:
                pubs.append(Publication.deserialize(db_pub["a"]))
        return pubs

    # Find publication by zip_path
    def query_pubs_by_zip(self, zip_path):
        cql_pubs = "MATCH (a:Publication) where a.zip_path=$zip_path return a"
        with self.driver.session() as session:
            nodes = session.run(cql_pubs, zip_path=zip_path)
            db_pubs = [record for record in nodes.data()]
            if len(db_pubs) > 0:
                return Publication.deserialize(db_pubs[0]["a"])
        return None

    # Retrieve all references
    def query_bib_refs(self, limit=None):
        refs = []
        cql_refs = "MATCH (a:Reference) return a"
        if limit is not None:
            cql_refs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_refs)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(Reference.deserialize(db_ref["a"]))
        return refs

    # Retrieve all index references
    def query_index_refs(self, limit=None):
        refs = []
        cql_refs = "MATCH (a:IndexReference) return a"
        if limit is not None:
            cql_refs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_refs)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(IndexReference.deserialize(db_ref["a"]))
        return refs

    # Retrieve bibliographic references for a publication
    def query_pub_bib_refs(self, pub_uuid):
        refs = []
        cql_pub_cites_ref = "MATCH (a:Publication)-[r:Cites]->(b:Reference) WHERE a.UUID = $pub_uuid return b"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_cites_ref, pub_uuid=pub_uuid)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(Reference.deserialize(db_ref["b"]))
        return refs

    # Retrieve index references for a publication
    def query_pub_index_refs(self, pub_uuid):
        refs = []
        cql_pub_includes_idx = "MATCH (a:Publication)-[r:Includes]->(b:IndexReference) WHERE a.UUID = $pub_uuid return b"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_includes_idx, pub_uuid=pub_uuid)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(IndexReference.deserialize(db_ref["b"]))
        return refs

