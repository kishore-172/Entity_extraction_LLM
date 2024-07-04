import streamlit as st
import json
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from pyvis.network import Network
from streamlit.components.v1 import html

# Function to create RDF graph from JSON data
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

    return g


# Function to visualize RDF graph using Pyvis
def visualize_pyvis_graph(data, rdf_graph):
    net = Network(notebook=True)
    for table in data['tables']:
        table_name = table['table_name']
        net.add_node(table_name, label=table_name, title=table['description'], color='#1f78b4')

        for column in table['columns']:
            column_name = column['name']
            net.add_node(column_name, label=column_name, title=column['description'], color='#33a02c')
            net.add_edge(table_name, column_name)

    return net


# Streamlit UI
def main():
    st.title("Knowledge Graph Visualization")

    # Load JSON data
    with open("data/cleaned_all_tables_data.json", 'r') as f:
        data = json.load(f)

    # Create RDF graph
    rdf_graph = create_rdf_graph(data)

    # Visualize RDF graph using Pyvis
    pyvis_graph = visualize_pyvis_graph(data, rdf_graph)

    # Display RDF graph using Pyvis
    st.subheader("Pyvis Visualization")
    pyvis_graph.show('knowledge_graph.html')
    html_file = open('knowledge_graph.html', 'r', encoding='utf-8').read()
    st.components.v1.html(html_file, width=1000, height=700, scrolling=True)

    # User query interface
    st.subheader("Query RDF Graph")

    # Prompt user to select a table
    selected_table = st.selectbox("Select a Table", [table['table_name'] for table in data['tables']])

    # Query columns based on selected table
    st.subheader(f"Columns of {selected_table}")
    for table in data['tables']:
        if table['table_name'] == selected_table:
            table_uri = URIRef("http://example.org/" + table['table_name'])
            query_result = rdf_graph.query(
                f"""
                SELECT ?column ?description
                WHERE {{
                    <{table_uri}> <http://example.org/hasColumn> ?column .
                    ?column rdfs:label ?label .
                    ?column <http://example.org/description> ?description .
                }}
                """
            )
            for row in query_result:
                column_name = row['column'].split('/')[-1]  # Extract only the column name
                st.write(f"Column: {column_name} - Description: {row['description']}")


if __name__ == "__main__":
    main()
