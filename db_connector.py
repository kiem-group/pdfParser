from neo4j import GraphDatabase


class DBConnector:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # def print_greeting(self, message):
    #     with self.driver.session() as session:
    #         greeting = session.write_transaction(self._create_and_return_greeting, message)
    #         print(greeting)
    #
    # @staticmethod
    # def _create_and_return_greeting(tx, message):
    #     result = tx.run("CREATE (a:Greeting) "
    #                     "SET a.message = $message "
    #                     "RETURN a.message + ', from node ' + id(a)", message=message)
    #     return result.single()[0]

    # Execute the CQL query
    def create_graph(self, pubs):
        # CQL to clear graph
        cql_delete_all = "MATCH (n) DETACH DELETE n"

        # CQL to create publication nodes
        cql_create_pub = """CREATE (a:Publication {0}) RETURN ID(a) as id"""

        # CQL to create publication industry identifier
        cql_create_id = """CREATE (b:Identifier {0}) RETURN ID(b) as id"""
        cql_create_pub_has_identifier = """MATCH (a:Publication), (b:Identifier)
           WHERE ID(a) = {0} AND ID(b) = {1} CREATE (a)-[r:HasIdentifier]->(b)"""

        # CQL to create publication contributor
        cql_create_contributor = """CREATE (b:Contributor {0}) RETURN ID(b) as id"""
        cql_create_pub_has_contributor = """MATCH (a:Publication), (b:Contributor)
                  WHERE ID(a) = {0} AND ID(b) = {1} CREATE (a)-[r:HasContributor]->(b)"""

        # CQL to create reference nodes
        cql_create_ref = """CREATE (b:Reference {0}) RETURN ID(b) as id"""
        cql_create_pub_cites_ref = """MATCH (a:Publication), (b:Reference)
           WHERE ID(a) = {0} AND ID(b) = {1} CREATE (a)-[r:Cites]->(b)"""

        # CQL to create external publications
        cql_create_ext_pub = """CREATE (b:ExternalPublication {0}) RETURN ID(b) as id"""
        cql_create_ref_refers_to_ext_pub = """MATCH (a:Reference), (b:ExternalPublication)
           WHERE ID(a) = {0} AND ID(b) = {1} CREATE (a)-[r:RefersTo]->(b)"""

        with self.driver.session() as session:
            # Clear graph
            session.run(cql_delete_all)
            # Create publications
            for pub in pubs:
                print("Creating Neo4j node for publication", pub.title)
                # Create publication
                res = session.run(cql_create_pub.format(pub.serialize()))
                pub_id = [record["id"] for record in res][0]
                # Create industry identifiers
                for industry_id in pub.identifiers:
                    res = session.run(cql_create_id.format(industry_id.serialize()))
                    id_id = [record["id"] for record in res][0]
                    session.run(cql_create_pub_has_identifier.format(pub_id, id_id))
                # Create editors
                for editor in pub.editors:
                    res = session.run(cql_create_contributor.format(editor.serialize()))
                    editor_id = [record["id"] for record in res][0]
                    session.run(cql_create_pub_has_contributor.format(pub_id, editor_id))
                # Create authors
                for author in pub.authors:
                    res = session.run(cql_create_contributor.format(author.serialize()))
                    author_id = [record["id"] for record in res][0]
                    session.run(cql_create_pub_has_contributor.format(pub_id, author_id))
                # Create references
                for ref in pub.bib_refs:
                    print("Creating Neo4j node for reference", ref.text)
                    res = session.run(cql_create_ref.format(ref.serialize()))
                    ref_id = [record["id"] for record in res][0]
                    session.run(cql_create_pub_cites_ref.format(pub_id, ref_id))
                    if ref.refers_to is not None:
                        for ext_pub in ref.refers_to:
                            res = session.run(cql_create_ext_pub.format(ext_pub.serialize()))
                            ext_pub_id = [record["id"] for record in res][0]
                            session.run(cql_create_ref_refers_to_ext_pub.format(ref_id, ext_pub_id))

    def query_graph(self):
        # CQL to retrieve publications
        cql_query_pubs = "MATCH (x:Publication) RETURN x"
        # CQL to retrieve references
        cql_query_refs = "MATCH (x:Reference) RETURN x"
        # CQL to retrieve references of a publication
        cql_query_pub_cites_ref = "MATCH (x:Publication)-[:Cites]->(y:Reference) RETURN y"

        with self.driver.session() as session:
            # Retrieve publications
            pubs = session.run(cql_query_pubs)
            print("List of publications present in the graph:")
            for pub in pubs:
                print(pub)

            # Retrieve references
            refs = session.run(cql_query_refs)
            print("List of references present in the graph:")
            for ref in refs:
                print(ref)

            # Query the citation relationships present in the graph
            rel_cites = session.run(cql_query_pub_cites_ref)
            print("Citation relationships present in the graph:")
            for r in rel_cites:
                print(r)