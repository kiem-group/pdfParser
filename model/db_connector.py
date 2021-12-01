from neo4j import GraphDatabase, Session
from model.publication import Publication
from model.reference_bibliographic import Reference
from model.reference_index import IndexReference
from model.publication_external import ExternalPublication
from model.index_external import ExternalIndex
from model.cluster_bibliographic import Cluster
from model.cluster_index import IndexCluster
from model.batch import Batch
from typing import List, Union


class DBConnector:

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # Delete

    def clear_graph(self, session: Session = None):
        if session is None:
            session = self.driver.session()
        cql_delete_relationships = "MATCH (a) -[r] -> () DELETE a, r"
        cql_delete_nodes = "MATCH (a) DELETE a"
        session.run(cql_delete_relationships)
        session.run(cql_delete_nodes)

    def delete_node(self, node_uuid: str, session: Session = None):
        if session is None:
            session = self.driver.session()
        cql_delete_relationships = "MATCH (a) -[r] -> () WHERE a.UUID = $node_uuid DELETE a, r"
        cql_delete_nodes = "MATCH (a) WHERE a.UUID = $node_uuid DELETE a"
        session.run(cql_delete_relationships, node_uuid=node_uuid)
        session.run(cql_delete_nodes, node_uuid=node_uuid)

    def delete_empty_nodes(self, node_class: str, session: Session = None):
        if session is None:
            session = self.driver.session()
        cql_delete_nodes = "MATCH (a: $node_class) DELETE a"
        session.run(cql_delete_nodes, node_class=node_class)

    def delete_pub(self, pub: Publication, session: Session = None):
        if session is None:
            session = self.driver.session()
        self.delete_node(pub.UUID, session)
        # Delete references
        if pub.bib_refs:
            for ref in pub.bib_refs:
                self.delete_node(ref.UUID, session)
        if pub.index_refs:
            for ref in pub.index_refs:
                self.delete_node(ref.UUID, session)
        # Delete lose external publications and index disambiguation links
        self.delete_empty_nodes("Reference")
        self.delete_empty_nodes("IndexReference")
        # Delete empty clusters
        self.delete_empty_nodes("Cluster")
        self.delete_empty_nodes("IndexCluster")

    # Create

    # Create publication nodes with relationships
    def create_pub(self, pub: Publication, session: Session = None):
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
    def create_bib_refs(self, pub: Publication, session: Session = None):
        if session is None:
            session = self.driver.session()
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
    def create_index_refs(self, pub: Publication, session: Session = None):
        if session is None:
            session = self.driver.session()
        cql_create_idx = """CREATE (:IndexReference {0})"""
        cql_create_pub_includes_idx = """MATCH (a:Publication), (b:IndexReference)
           WHERE a.UUID = $pub_uuid AND b.UUID = $ref_uuid CREATE (a)-[:Includes]->(b)"""
        for idx in pub.index_refs:
            session.run(cql_create_idx.format(idx.serialize()))
            session.run(cql_create_pub_includes_idx, pub_uuid=pub.UUID, ref_uuid=idx.UUID)
            if idx.refers_to is not None:
                for ext_idx in idx.refers_to:
                    self.create_ext_index(ext_idx, idx.UUID, session)

    # Create external publications that disambiguate references
    def create_ext_pub(self, ext_pub: ExternalPublication, ref_uuid: str, session: Session = None):
        if session is None:
            session = self.driver.session()
        # TODO check if it already exists?
        cql_create_ext_pub = """CREATE (b:ExternalPublication {0})"""
        cql_create_ref_refers_to_ext_pub = """MATCH (a:Reference), (b:ExternalPublication)
           WHERE a.UUID = $ref_uuid AND b.UUID = $ext_pub_uuid CREATE (a)-[:RefersTo]->(b)"""
        session.run(cql_create_ext_pub.format(ext_pub.serialize()))
        session.run(cql_create_ref_refers_to_ext_pub, ref_uuid=ref_uuid, ext_pub_uuid=ext_pub.UUID)

    # Create external nodes that disambiguate index references
    def create_ext_index(self, ext_idx: ExternalIndex, ref_uuid: str, session: Session = None):
        if session is None:
            session = self.driver.session()
        # TODO check if it already exists?
        cql_create_ext_idx = """CREATE (b:ExternalIndex {0})"""
        cql_create_ref_refers_to_ext_idx = """MATCH (a:IndexReference), (b:ExternalIndex)
           WHERE a.UUID = $ref_uuid AND b.UUID = $ext_pub_uuid CREATE (a)-[:RefersTo]->(b)"""
        session.run(cql_create_ext_idx.format(ext_idx.serialize()))
        session.run(cql_create_ref_refers_to_ext_idx, ref_uuid=ref_uuid, ext_pub_uuid=ext_idx.UUID)

    # Create cluster of bibliographic references
    def create_cluster(self, cluster: Cluster, session: Session = None):
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

    # Create cluster of index references
    def create_index_cluster(self, cluster: IndexCluster, session: Session = None):
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

    # Create batch clusters
    def create_clusters(self, batch: Batch, session: Session = None):
        if session is None:
            session = self.driver.session()
        # Add bibliographic clusters
        if batch.cluster_set_bib and batch.cluster_set_bib.clusters:
            for cluster in batch.cluster_set_bib.clusters:
                self.create_cluster(cluster, session)
        # Add index clusters
        if batch.cluster_set_index and batch.cluster_set_index.clusters:
            for cluster in batch.cluster_set_index.clusters:
                self.create_cluster(cluster, session)

    # Create knowledge graph
    def create_graph(self, batch: Batch):
        with self.driver.session() as session:
            # Create publications
            if batch.publications:
                for pub in batch.publications:
                    try:
                        self.create_pub(pub, session)
                    except:
                        print("Failed to serialize publication: ", pub.UUID)
            self.create_clusters(batch, session)

    # Query

    # Retrieve all publications
    def query_pubs(self, limit: int = None) -> List[Publication]:
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

    # Find node by uuid
    def query_pub(self, node_uuid: str) -> Union[Publication, None]:
        cql_pubs = "MATCH (a) where a.UUID=$node_uuid return a"
        with self.driver.session() as session:
            nodes = session.run(cql_pubs, node_uuid=node_uuid)
            db_pubs = [record for record in nodes.data()]
            if len(db_pubs) > 0:
                return Publication.deserialize(db_pubs[0]["a"])
        return None

    # Find publication by zip_path
    def query_pub_by_zip(self, zip_path: str) -> Union[Publication, None]:
        cql_pubs = "MATCH (a:Publication) where a.zip_path=$zip_path return a"
        with self.driver.session() as session:
            nodes = session.run(cql_pubs, zip_path=zip_path)
            db_pubs = [record for record in nodes.data()]
            if len(db_pubs) > 0:
                return Publication.deserialize(db_pubs[0]["a"])
        return None

    # Retrieve all references
    def query_bib_refs(self, limit: int = None) -> List[Reference]:
        refs = []
        cql_refs = "MATCH (a:Reference) return a"
        if limit:
            cql_refs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_refs)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(Reference.deserialize(db_ref["a"]))
        return refs

    # Retrieve all index references
    def query_index_refs(self, limit: int = None) -> List[IndexReference]:
        refs = []
        cql_refs = "MATCH (a:IndexReference) return a"
        if limit:
            cql_refs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_refs)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(IndexReference.deserialize(db_ref["a"]))
        return refs

    # Retrieve bibliographic references for a publication
    def query_pub_bib_refs(self, pub_uuid: str) -> List[Reference]:
        refs = []
        cql_pub_cites_ref = "MATCH (a:Publication)-[r:Cites]->(b:Reference) WHERE a.UUID = $pub_uuid return b"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_cites_ref, pub_uuid=pub_uuid)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(Reference.deserialize(db_ref["b"]))
        return refs

    # Retrieve index references for a publication
    def query_pub_index_refs(self, pub_uuid: str) -> List[IndexReference]:
        refs = []
        cql_pub_incl_idx = "MATCH (a:Publication)-[r:Includes]->(b:IndexReference) WHERE a.UUID = $pub_uuid return b"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_incl_idx, pub_uuid=pub_uuid)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(IndexReference.deserialize(db_ref["b"]))
        return refs

    # Retrieve bibliographic references for a cluster
    def query_cluster_bib_refs(self, cluster_uuid: str) -> List[Reference]:
        refs = []
        cql_pub_cites_ref = "MATCH (a:Reference)-[r:BelongsTo]->(b:Cluster) WHERE b.UUID = $cluster_uuid return a"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_cites_ref, cluster_uuid=cluster_uuid)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(Reference.deserialize(db_ref["a"]))
        return refs

    # Retrieve bibliographic references for a cluster
    def query_cluster_index_refs(self, cluster_uuid: str) -> List[IndexReference]:
        refs = []
        cql_pub_cites_ref = "MATCH (a:IndexReference)-[r:BelongsTo]->(b:IndexCluster) WHERE b.UUID = $cluster_uuid return a"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_cites_ref, cluster_uuid=cluster_uuid)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(IndexReference.deserialize(db_ref["a"]))
        return refs

    # Retrieve all bibliographic clusters
    def query_clusters(self, limit: int = None) -> List[Cluster]:
        clusters = []
        cql_refs = "MATCH (a:Cluster) return a"
        if limit:
            cql_refs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_refs)
            db_clusters = [record for record in nodes.data()]
            for db_cluster in db_clusters:
                refs = self.query_cluster_bib_refs(db_cluster["a"]["UUID"])
                clusters.append(Cluster.deserialize(db_cluster["a"], refs))
        return clusters

    # Retrieve all bibliographic clusters
    def query_index_clusters(self, limit: int = None) -> List[IndexCluster]:
        clusters = []
        cql_refs = "MATCH (a:IndexCluster) return a"
        if limit:
            cql_refs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_refs)
            db_clusters = [record for record in nodes.data()]
            for db_cluster in db_clusters:
                refs = self.query_cluster_index_refs(db_cluster["a"]["UUID"])
                clusters.append(IndexCluster.deserialize(db_cluster["a"], refs))
        return clusters

    def query_node_count(self) -> int:
        cql_pubs = "MATCH (a) return count(a)"
        with self.driver.session() as session:
            count = session.run(cql_pubs)
            print(count)
            return count
        return 0
