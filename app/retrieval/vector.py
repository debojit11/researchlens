from pathlib import Path
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import CHROMA_DIR

COLLECTION_NAME= "researchlens_docs"


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")


def create_vector_store(chunks):
    embeddings=get_embeddings()

    vector_store= Chroma.from_documents(documents=chunks,
                                    embedding=embeddings,
                                    collection_name=COLLECTION_NAME,
                                    persist_directory=str(CHROMA_DIR))

    return vector_store



def load_vector_store():
    embeddings = get_embeddings()

    vector_store= Chroma(collection_name=COLLECTION_NAME,
                        embedding_function= embeddings,
                        persist_directory=str(CHROMA_DIR))
    
    return vector_store



def vector_store_exists():
    path= Path(CHROMA_DIR)

    return path.exists() and any(path.iterdir())



def vector_search(vector_store, query:str , k: int=3):
    return vector_store.similarity_search(query, k=k)