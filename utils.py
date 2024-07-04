from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from pyvis.network import Network

def create_rdf_graph(data):
    g = Graph()
    namespace = "http://example.org/"

    for table in data['tables']:
        table_uri = URIRef(namespace + table['table_name'])
        g.add((table_uri, RDF.type, URIRef(namespace + "Table")))
        g.add((table_uri, RDFS.label, Literal(table['table_name'])))
        g.add((table_uri, URIRef(namespace + "description"), Literal(table['description'])))

        for column in table['columns']:
            column_uri = URIRef(namespace + column['name'])
            g.add((column_uri, RDF.type, URIRef(namespace + "Column")))
            g.add((column_uri, RDFS.label, Literal(column['name'])))
            g.add((column_uri, URIRef(namespace + "description"), Literal(column['description'])))
            g.add((table_uri, URIRef(namespace + "hasColumn"), column_uri))

    return g, namespace

def visualize_pyvis_graph(rdf_graph, namespace, query_tables):
    net = Network(notebook=True)
    added_nodes = set()

    for s, p, o in rdf_graph:
        if isinstance(o, URIRef):
            if (s, RDF.type, URIRef(namespace + "Table")) in rdf_graph and str(rdf_graph.value(s, RDFS.label)) in query_tables:
                table_name = str(rdf_graph.value(s, RDFS.label))
                table_description = str(rdf_graph.value(s, URIRef(namespace + "description")))
                if table_name not in added_nodes:
                    net.add_node(table_name, label=table_name, title=table_description, color='#1f78b4')
                    added_nodes.add(table_name)

    for s, p, o in rdf_graph:
        if isinstance(o, URIRef):
            if (s, RDF.type, URIRef(namespace + "Column")) in rdf_graph:
                column_name = str(rdf_graph.value(s, RDFS.label))
                column_description = str(rdf_graph.value(s, URIRef(namespace + "description")))
                table_uri = next(rdf_graph.subjects(URIRef(namespace + "hasColumn"), s))
                table_name = str(rdf_graph.value(table_uri, RDFS.label))
                if table_name in query_tables and column_name not in added_nodes:
                    net.add_node(column_name, label=column_name, title=column_description, color='#33a02c')
                    added_nodes.add(column_name)
                    if table_name in net.get_nodes():
                        net.add_edge(table_name, column_name)

    return net

def query_rdf_graph_for_columns(rdf_graph, namespace, table_name):
    query = f"""
    SELECT ?column ?column_label ?description
    WHERE {{
        ?table rdf:type <{namespace}Table> .
        ?table rdfs:label "{table_name}" .
        ?table <{namespace}hasColumn> ?column .
        ?column rdfs:label ?column_label .
        ?column <{namespace}description> ?description .
    }}
    """
    results = rdf_graph.query(query)
    columns = []
    for row in results:
        columns.append((str(row['column_label']), str(row['description'])))
    return columns
