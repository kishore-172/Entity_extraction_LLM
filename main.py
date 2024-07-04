import streamlit as st
import json
from langchain import LangChain
import faiss

# Load the JSON data
with open('data/all_tables_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Initialize LangChain for natural language processing
lang_chain = LangChain()


# Function to tokenize and embed text using LangChain
def embed_text(text):
    tokens = lang_chain.tokenize(text)
    embeddings = lang_chain.embed(tokens)
    return embeddings


# Function to recommend tables and columns based on user query
def recommend_tables_columns(query, data, k=5):
    # Embedding the query
    query_embedding = embed_text(query)

    # Embedding tables and columns descriptions
    table_descriptions = [table['description'] for table in data['tables']]
    table_embeddings = [embed_text(desc) for desc in table_descriptions]

    # Flattening column descriptions
    column_descriptions = []
    for table in data['tables']:
        for col in table['columns']:
            column_descriptions.append(col['description'])
    column_embeddings = [embed_text(desc) for desc in column_descriptions]

    # Flatten embeddings for faiss
    table_flat = faiss.vector_to_array(table_embeddings).reshape(len(table_embeddings), -1)
    column_flat = faiss.vector_to_array(column_embeddings).reshape(len(column_embeddings), -1)

    # Concatenate table and column embeddings
    table_and_column_embeddings = faiss.vector_to_array(table_embeddings + column_embeddings).reshape(
        len(table_embeddings) + len(column_embeddings), -1)

    # Perform faiss similarity search
    index = faiss.IndexFlatL2(table_and_column_embeddings.shape[1])
    index.add(table_and_column_embeddings)
    _, indices = index.search(query_embedding, k)

    # Retrieve recommended tables and columns
    recommendations = []
    for idx in indices[0]:
        if idx < len(table_descriptions):
            recommendations.append((data['tables'][idx]['table_name'], 'Table'))
        else:
            col_idx = idx - len(table_descriptions)
            table_idx = col_idx // len(data['tables'][0]['columns'])
            col_name = data['tables'][table_idx]['columns'][col_idx % len(data['tables'][0]['columns'])]['name']
            recommendations.append((data['tables'][table_idx]['table_name'], col_name))

    return recommendations


# Streamlit UI
def main():
    st.title('Column and Table Recommendation App')
    query = st.text_input('Enter your query:', '')

    if st.button('Recommend'):
        if query:
            recommendations = recommend_tables_columns(query, data)
            st.subheader('Recommendations:')
            for recommendation in recommendations:
                st.write(f"- {recommendation[0]} ({recommendation[1]})")


if __name__ == '__main__':
    main()
