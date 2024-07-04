import streamlit as st
import json
import openai
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import os
from utils import create_rdf_graph, visualize_pyvis_graph, query_rdf_graph_for_columns
from streamlit.components.v1 import html

# Load environment variables from .env file
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')


# Load the JSON data
def load_data():
    try:
        with open("data/all_tables_data.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Error: Data file 'all_tables_data.json' not found.")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON data: {str(e)}")
        return None


# Initialize LangChain components with error handling
def initialize_langchain(data):
    try:
        if not data:
            st.warning("No data loaded. LangChain initialization skipped.")
            return None

        documents = []
        for table in data['tables']:
            table_info = f"Table: {table['table_name']}\nDescription: {table['description']}\nColumns: {', '.join([col['name'] + ' (' + col['description'] + ')' for col in table['columns']])}\n"
            documents.append(table_info)

        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectorstore = FAISS.from_texts(documents, embeddings)

        llm = OpenAI(api_key=openai_api_key)
        retriever = vectorstore.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever, chain_type="stuff",
                                               return_source_documents=True)

        return qa_chain
    except Exception as e:
        st.error(f"Error initializing LangChain components: {str(e)}")
        return None


# Function to suggest tables and columns for analysis based on query
def suggest_tables_and_columns(query, chain, rdf_graph, namespace):
    suggested_tables = []
    suggested_columns = []

    if chain:
        try:
            result = chain({"query": query})
            if result and 'source_documents' in result:
                for doc in result['source_documents']:
                    lines = doc.page_content.split("\n")
                    for line in lines:
                        if line.startswith("Table:"):
                            suggested_tables.append(line.split(": ")[1])
                        elif line.startswith("Columns:"):
                            columns = line.split(": ")[1].split(", ")
                            suggested_columns.extend(columns)
        except Exception as e:
            st.error(f"Error occurred during query processing: {str(e)}")
    else:
        st.error("Error: LangChain components failed to initialize. Please check your environment configuration.")

    # Refine suggested columns using RDF graph
    refined_columns = []
    for table in suggested_tables:
        columns = query_rdf_graph_for_columns(rdf_graph, namespace, table)
        refined_columns.extend(columns)

    # Score and filter columns based on relevance
    helpful_columns = filter_helpful_columns(refined_columns)

    return suggested_tables, helpful_columns

def filter_helpful_columns(columns):
    # Define keywords or criteria indicative of helpful columns for analysis
    keywords = ["id", "date", "amount", "name", "type", "status", "count", "total", "average"]

    scored_columns = []
    for col, desc in columns:
        score = sum(1 for keyword in keywords if keyword in col.lower() or keyword in desc.lower())
        scored_columns.append((col, desc, score))

    # Sort columns by score in descending order and take the top N (e.g., top 5) most relevant columns
    top_columns = sorted(scored_columns, key=lambda x: x[2], reverse=True)[:5]
    return [(col, desc) for col, desc, score in top_columns]

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = load_data()

if 'rdf_graph' not in st.session_state and st.session_state.data:
    st.session_state.rdf_graph, st.session_state.namespace = create_rdf_graph(st.session_state.data)

if 'chain' not in st.session_state:
    st.session_state.chain = initialize_langchain(st.session_state.data)

if 'history' not in st.session_state:
    st.session_state.history = []

# Streamlit UI
st.title("Knowledge Base: Suggested Tables and Columns")

# Query input
query = st.text_input("Enter your query:", "")

# Submit query
if st.button("Submit"):
    chain = st.session_state.chain

    if chain is not None:
        suggested_tables, suggested_columns = suggest_tables_and_columns(query, chain, st.session_state.rdf_graph,
                                                                         st.session_state.namespace)

        # Display suggested tables and columns in a tabular format
        st.subheader("Suggested Tables for Analysis")
        if suggested_tables:
            st.table({"Tables": suggested_tables})
        else:
            st.write("No suggested tables found based on the query and LLM output.")

        st.subheader("Suggested Columns for Analysis")
        if suggested_columns:
            st.table({"Columns": [col[0] for col in suggested_columns],
                      "Descriptions": [col[1] for col in suggested_columns]})
        else:
            st.write("No suggested columns found based on the query and LLM output.")

        # Visualize RDF graph using Pyvis for the suggested tables and columns
        if suggested_tables:
            pyvis_graph = visualize_pyvis_graph(st.session_state.rdf_graph, st.session_state.namespace,
                                                suggested_tables)
            st.subheader("Knowledge Graph Visualization")
            pyvis_graph.show('knowledge_graph.html')
            with open('knowledge_graph.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            html(html_content, width=1000, height=700, scrolling=True)

        # Log the query and response to history
        st.session_state.history.append((query, (suggested_tables, suggested_columns)))
    else:
        st.error("Error: LangChain components failed to initialize. Please check your environment configuration.")

# Display query history
st.subheader("Query History")
for i, (qry, (suggested_tables, suggested_columns)) in enumerate(st.session_state.history):
    st.write(f"**Query {i + 1}:** {qry}")
    st.write("**Suggested Tables:**")
    if suggested_tables:
        st.table({"Tables": suggested_tables})
    else:
        st.write("No suggested tables found for this query.")

    st.write("**Suggested Columns:**")
    if suggested_columns:
        st.table({"Columns": [col[0] for col in suggested_columns], "Descriptions": [col[1] for col in suggested_columns]})
    else:
        st.write("No suggested columns found for this query.")
