# author: Natallia Kokash, natallia.kokash@gmail.com
# Maps KIEM resources to Neo4j graph

from neo4j import GraphDatabase, Session
from model.publication_base import BasePublication
from model.publication import Publication
from model.contributor import Contributor
from model.industry_identifier import IndustryIdentifier
from model.reference_bibliographic import Reference
from model.reference_index import IndexReference
from model.publication_external import ExternalPublication
from model.index_external import ExternalIndex
from model.cluster_bibliographic import Cluster
from model.cluster_index import IndexCluster
from model.batch import Batch
from typing import List, Union
import logging
import uuid


class DBConnector:

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.logger = logging.getLogger('pdfParser.dbConnector.' + self.__class__.__name__)
        # self.logger.debug('Created an instance of: %s ', self.__class__.__name__)

    def cdisconnected(self):
        self.driver.cdisconnected()

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
        cql_delete_nodes = "MATCH (a {UUID: $node_uuid}) DETACH DELETE a"
        session.run(cql_delete_nodes, node_uuid=node_uuid)

    def detach_delete_nodes(self, node_class: str, session: Session = None):
        if session is None:
            session = self.driver.session()
        cql_delete_nodes = "MATCH (a: {node_class}) DETACH DELETE a".format(node_class=node_class)
        session.run(cql_delete_nodes)

    def delete_empty_nodes(self, node_class: str, session: Session = None):
        if session is None:
            session = self.driver.session()
        cql_delete_nodes = "MATCH (a: {node_class}) WHERE size((a)--())=0 DELETE a".format(node_class=node_class)
        session.run(cql_delete_nodes)

    # Delete external publications
    def delete_external_pub(self, session: Session = None):
        if session is None:
            session = self.driver.session()
        cql_delete_relationships = "MATCH (a:ExternalPublication) -[r:HasContributor] -> (b:Contributor) DELETE r"
        session.run(cql_delete_relationships)
        self.delete_empty_nodes("Contributor")
        self.detach_delete_nodes("ExternalPublication")

    # Delete external indices
    def delete_external_index(self, session: Session = None):
        if session is None:
            session = self.driver.session()
        self.detach_delete_nodes("ExternalIndex")

    # Delete external references (disambiguation results)
    def delete_external(self, session: Session = None):
        if session is None:
            session = self.driver.session()
        self.delete_external_pub(session)
        self.delete_external_index(session)

    def delete_pub(self, pub: Publication, session: Session = None):
        if session is None:
            session = self.driver.session()

        self.logger.debug("# nodes before deleting publication data: %d", self.query_node_count())

        self.delete_node(pub.UUID, session)

        # Delete disconnected contributors
        self.delete_empty_nodes(Contributor.__name__)

        # Delete disconnected industry identifiers
        # TODO remove obsolete class 'Identifier'
        self.delete_empty_nodes("Identifier")
        self.delete_empty_nodes(IndustryIdentifier.__name__)

        # Delete references
        if pub.bib_refs:
            for ref in pub.bib_refs:
                self.delete_node(ref.UUID, session)
        self.delete_empty_nodes(Reference.__name__)

        if pub.index_refs:
            for ref in pub.index_refs:
                self.delete_node(ref.UUID, session)
        self.delete_empty_nodes(IndexReference.__name__)

        # TODO test if this works as references are connected to clusters

        # Delete disconnected external publications and external index references
        self.delete_empty_nodes(ExternalPublication.__name__)

        self.delete_empty_nodes(ExternalIndex.__name__)

        # Delete empty clusters
        self.delete_empty_nodes(Cluster.__name__)

        self.delete_empty_nodes(IndexCluster.__name__)

        self.logger.debug("# nodes after deleting publication data: %d", self.query_node_count())

    # Create

    # Create publication nodes with relationships
    def create_pub(self, pub: Publication, session: Session = None):
        if session is None:
            session = self.driver.session()
        # TODO create or update

        self.logger.debug("# nodes before adding publication data: %d", self.query_node_count())

        # Create publication
        cql_create_pub = """CREATE (:Publication {0})"""
        session.run(cql_create_pub.format(pub.serialize()))

        # Create industry identifiers
        cql_create_id = """CREATE (:IndustryIdentifier {0})"""
        cql_create_pub_has_identifier = """MATCH (a:Publication), (b:IndustryIdentifier)
           WHERE a.UUID = $pub_uuid AND b.UUID = $id_uuid CREATE (a)-[:HasIdentifier]->(b)"""
        for industry_id in pub.identifiers:
            session.run(cql_create_id.format(industry_id.serialize()))
            session.run(cql_create_pub_has_identifier, pub_uuid=pub.UUID, id_uuid=industry_id.UUID)
        # Create contributors: editors or authors
        self.create_contributor(pub, session)
        # Create bibliographic references
        self.create_bib_refs(pub, session)
        # Create index references
        self.create_index_refs(pub, session)
        self.logger.debug("# nodes after adding publication data: %d", self.query_node_count())

    def create_contributor(self, pub: BasePublication, session: Session = None):
        if session is None:
            session = self.driver.session()
        # TODO check whether contributor already exists?
        # Create contributors: editors or authors
        cql_create_contributor = """CREATE (:Contributor {0})"""
        cql_create_pub_has_contributor = """MATCH (a), (b:Contributor)
                  WHERE a.UUID = $pub_uuid AND b.UUID = $c_uuid CREATE (a)-[:HasContributor {num: $num}]->(b)"""
        # Create editors
        if pub.editors:
            for idx, editor in enumerate(pub.editors):
                session.run(cql_create_contributor.format(editor.serialize()))
                session.run(cql_create_pub_has_contributor, pub_uuid=pub.UUID, c_uuid=editor.UUID, num=idx)
        # Create authors
        if pub.authors:
            for idx, author in enumerate(pub.authors):
                session.run(cql_create_contributor.format(author.serialize()))
                session.run(cql_create_pub_has_contributor, pub_uuid=pub.UUID, c_uuid=author.UUID, num=idx)

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
            # Enable to save "follows" relationship (redundant in practice)
            # if ref.follows is not None:
            #     cql_create_ref_follows = """MATCH (a:Reference), (b:Reference)
            #        WHERE a.UUID = $a_uuid AND b.UUID = $b_uuid CREATE (a)-[:Follows]->(b)"""
            #     session.run(cql_create_ref_follows, a_uuid=ref.UUID, b_uuid=ref.follows.UUID)

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
        # Create contributors: editors or authors
        self.create_contributor(ext_pub, session)

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
                        self.logger.error("Failed to serialize publication: %s", pub.UUID)
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

    # Retrieve bibliographic references for a publication
    def query_pub_bib_refs(self, pub_uuid: str) -> List[Reference]:
        refs = []
        cql_pub_cites_ref = "MATCH (a:Publication)-[r:Cites]->(b:Reference) WHERE a.UUID = $pub_uuid RETURN b " \
                            "ORDER BY b.ref_num"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_cites_ref, pub_uuid=pub_uuid)
            db_refs = [record for record in nodes.data()]
            for idx, db_ref in enumerate(db_refs):
                ref = Reference.deserialize(db_ref["b"])
                refs.append(ref)
                if ref.text.startswith('——') and idx > 0:
                    ref.follows = refs[idx - 1]
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

    # Retrieve publication identifiers
    def query_pub_identifiers(self, pub_uuid: str) -> List[IndustryIdentifier]:
        identifiers = []
        cql_pub_incl_idx = "MATCH (a:Publication)-[r:HasIdentifier]->(b:IndustryIdentifier) WHERE a.UUID = $pub_uuid return b"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_incl_idx, pub_uuid=pub_uuid)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                identifiers.append(IndustryIdentifier.deserialize(db_ref["b"]))
        return identifiers

    # Retrieve publication contributors
    def query_pub_contributors(self, pub_uuid: str) -> List[Contributor]:
        contributors = []
        cql_pub_incl_idx = "MATCH (a:Publication)-[r:HasContributor]->(b:Contributor) WHERE a.UUID = $pub_uuid return b"
        with self.driver.session() as session:
            nodes = session.run(cql_pub_incl_idx, pub_uuid=pub_uuid)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                contributors.append(Contributor.deserialize(db_ref["b"]))
        return contributors

    # Retrieve publication with all relationships
    def query_pub_full(self, node_uuid: str) -> Union[Publication, None]:
        pub = self.query_pub(node_uuid)
        if pub is not None:
            # industry identifiers
            pub.identifiers = self.query_pub_identifiers(pub.UUID)
            # contributors
            contributors = self.query_pub_contributors(pub.UUID)
            pub.authors = []
            pub.editors = []
            for contributor in contributors:
                if "author" in contributor.type:
                    pub.authors.append(contributor)
                else:
                    if "editor" in contributor.type:
                        pub.editors.append(contributor)
            # bibliographic references
            pub.bib_refs = self.query_pub_bib_refs(pub.UUID)
            # index references
            pub.index_refs = self.query_pub_index_refs(pub.UUID)
            return pub
        return None

    def query_resource(self, cql_refs: str, cls, limit: int = None):
        refs = []
        if limit:
            cql_refs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_refs)
            db_refs = [record for record in nodes.data()]
            for db_ref in db_refs:
                refs.append(cls.deserialize(db_ref["a"]))
        return refs

    # Retrieve all references
    def query_bib_refs(self, limit: int = None) -> List[Reference]:
        cql_refs = "MATCH (a:Reference) return a"
        return self.query_resource(cql_refs, Reference, limit)

    # Retrieve all index references
    def query_index_refs(self, limit: int = None) -> List[IndexReference]:
        cql_refs = "MATCH (a:IndexReference) return a"
        return self.query_resource(cql_refs, IndexReference, limit)

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

    # Retrieve index references for a cluster
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
    def query_clusters(self, include_refs: bool = True, limit: int = None) -> List[Cluster]:
        clusters = []
        cql_refs = "MATCH (a:Cluster) return a"
        if limit:
            cql_refs += " limit " + str(limit)
        with self.driver.session() as session:
            nodes = session.run(cql_refs)
            db_clusters = [record for record in nodes.data()]
            if include_refs:
                for db_cluster in db_clusters:
                    refs = self.query_cluster_bib_refs(db_cluster["a"]["UUID"])
                    clusters.append(Cluster.deserialize(db_cluster["a"], refs))
        return clusters

    def merge_clusters(self, threshold: float = 0.9):
        clusters = self.query_clusters(include_refs=False)
        start = 0
        end = len(clusters)
        batch_UUID = str(uuid.uuid4())
        while start < end:
            c1 = clusters[start]
            c2 = clusters[end]
            merge = c1.batch is None or c2.batch is None or c1.batch != c2.batch
            if merge:
                c1.refs = self.query_cluster_bib_refs(c1.UUID)
                c2.refs = self.query_cluster_bib_refs(c2.UUID)
                if c1.ref_lev_ratio(c2.refs[0], False) > threshold:
                    c_new = Cluster(batch=batch_UUID, refs=[*c1.refs, *c2.refs])
                    # TODO update cluster: reconnect references to c1, delete c2
                    pass

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
        cql_count = "MATCH (a) return count(a) as node_count"
        with self.driver.session() as session:
            res = session.run(cql_count)
            entries = [record for record in res.data()]
            return entries[0]['node_count']

    def query_rel_count(self) -> int:
        cql_count = "MATCH ()-->() RETURN COUNT(*) AS rel_count"
        with self.driver.session() as session:
            res = session.run(cql_count)
            entries = [record for record in res.data()]
            return entries[0]['rel_count']
