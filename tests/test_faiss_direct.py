import os
import faiss
import pickle
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

def test_faiss_save():
    print("Testing FAISS save...")
    embeddings = OpenAIEmbeddings()
    docs = [Document(page_content="Hello world", metadata={"source": "test"})]
    
    print("Creating vector store...")
    vector_store = FAISS.from_documents(docs, embeddings)
    
    index_path = "data/test_faiss_index"
    print(f"Saving to {index_path}...")
    vector_store.save_local(index_path)
    
    if os.path.exists(index_path):
        print(f"✅ Created {index_path}")
        print(f"Contents: {os.listdir(index_path)}")
    else:
        print(f"❌ Failed to create {index_path}")

if __name__ == "__main__":
    test_faiss_save()
