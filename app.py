import streamlit as st
import PyPDF2
import cohere
from pinecone import Pinecone
import textwrap

# Initialize Cohere and Pinecone
co = cohere.Client(api_key = 's1gcHF8Dhz2ct0iyHoQYPOReVKHzBapb9BMTrLiK',)
pc = Pinecone(api_key= '8c3a1f42-35f5-4778-81d7-1c4e0b334326')
index = pc.Index('example-index')

def create_index():
  pc.create_index(
      name="example-index",
      dimension=4096,
      metric="cosine",
      spec=ServerlessSpec(
          cloud='aws',
          region='us-east-1'
      )
  )

def embed_text(text):
    response = co.embed(texts=[text], model="embed-english-v2.0")
    return response.embeddings[0]

def chunk_text(text, chunk_size=512):
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def upload_and_process_pdf(file):
    pdf_reader = PyPDF2. PdfReader(file)
    text = ''
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()

    # Chunk the text into smaller parts
    chunks = chunk_text(text, chunk_size=512)
    
    # Embed and store each chunk in Pinecone
    for i, chunk in enumerate(chunks):
        chunk_embedding = co.embed(texts=[chunk], model="embed-english-v2.0").embeddings[0]
        index.upsert([(f"{file.name}_{i}", chunk_embedding)])
    
    return chunks

def get_answer(query, chunks):
    query_embedding = embed_text(query)
    
    # Retrieve top 3 relevant chunks
    top_k = 3
    result = index.query(vector=query_embedding, top_k=top_k)
    retrieved_chunks = [match['id'] for match in result['matches']]

    # Get the actual text for each retrieved chunk
    relevant_texts = [chunks[int(match['id'].split('_')[-1])] for match in result['matches']]
    
    # Use the retrieved chunks as context for the answer generation
    context = ' '.join(relevant_texts)
    response = co.generate(prompt=f"{context}\n\nQuestion: {query}\nAnswer:", max_tokens=100)
    return response.generations[0].text, relevant_texts

st.title("Interactive QA Bot")

# Upload PDF
def main():
    # st.set_page_config("QA with Aryan")
    st.header("ChatBot")

    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file is not None:
        document_text = upload_and_process_pdf(uploaded_file)

        # Ask a question
        query = st.text_input("Ask a question about the document:")
        if query:
            answer, relevent_texts = get_answer(query, document_text)
            st.write("Answer:", answer)
            text = textwrap.indent('\n'.join(relevent_texts), '> ', predicate=lambda _: True)
            st.markdown(f"**Relevant Texts:**\n\n{text}")

if __name__=="__main__":
    main()  