import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")

def get_embeddings():
    # Using a multilingual model that works well with Indonesian
    return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def get_vectorstore(collection_name: str = "course_materials") -> Chroma:
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_PERSIST_DIR
    )

def index_material(content: str, metadata: dict):
    """
    Chunks and indexes a string of content into ChromaDB.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    docs = text_splitter.create_documents([content], metadatas=[metadata])
    
    vectorstore = get_vectorstore()
    vectorstore.add_documents(docs)
    
    return len(docs)

def retrieve_materials(query: str, course_id: str = None, k: int = 3):
    """
    Retrieves the most relevant chunks for a given query and course.
    """
    vectorstore = get_vectorstore()
    filter_dict = {"course_id": course_id} if course_id else None
    
    results = vectorstore.similarity_search(
        query=query,
        k=k,
        filter=filter_dict
    )
    return results
