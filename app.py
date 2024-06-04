import streamlit as st
import json
import openai
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

# Load the JSON data
def load_data():
    with open("data/all_tables_data.json", 'r') as f:
        return json.load(f)

# Initialize LangChain components
def initialize_langchain(data):
    documents = []
    for table in data['tables']:
        table_info = f"Table: {table['table_name']}\nDescription: {table['description']}\nColumns: {', '.join([col['name'] + ' (' + col['description'] + ')' for col in table['columns']])}\n"
        documents.append(table_info)

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.from_texts(documents, embeddings)

    llm = OpenAI(api_key=openai_api_key)
    retriever = vectorstore.as_retriever()
    qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever, chain_type="stuff", return_source_documents=True)

    return qa_chain

# Function to suggest tables and columns for analysis based on query
# Function to suggest tables and columns for analysis based on query
def suggest_tables_and_columns(query, data):
    suggested_tables = []
    suggested_columns = []

    # Implement your logic here to suggest tables and columns based on the query
    # For demonstration purposes, let's assume we suggest tables and columns that contain the query term
    for table in data['tables']:
        if query.lower() in table['table_name'].lower():
            suggested_tables.append(table['table_name'])
            suggested_columns.extend([col['name'] for col in table['columns'] if query.lower() in col['name'].lower()])

    return suggested_tables, suggested_columns


# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = load_data()

if 'chain' not in st.session_state:
    st.session_state.chain = initialize_langchain(st.session_state.data)

if 'history' not in st.session_state:
    st.session_state.history = []

# Streamlit UI
st.title("Knowledge Base:DRS")

# Query input
query = st.text_input("Enter your query:", "")

# Submit query
if st.button("Submit"):
    chain = st.session_state.chain
    result = chain({"query": query})
    response = result.get("result", "No response generated")
    st.session_state.history.append((query, response))

    # Suggest tables and columns based on query
    suggested_tables, suggested_columns = suggest_tables_and_columns(query, st.session_state.data)

    # Display suggested tables and columns
    st.subheader("Suggested Tables for Analysis")
    for table in suggested_tables:
        st.write(table)

    st.subheader("Suggested Columns for Analysis")
    for column in suggested_columns:
        st.write(column)

# Display query history
st.subheader("Query History")
for i, (qry, rsp) in enumerate(st.session_state.history):
    st.write(f"**Query {i + 1}:** {qry}")
    st.write(f"**Response:** {rsp}")
