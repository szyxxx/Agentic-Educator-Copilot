import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings
from app.core import config

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR") or os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")

def get_embeddings():
    if config.EMBEDDING_PROVIDER == "ollama":
        # bge-m3 is multilingual; release it after use on memory-limited GPUs.
        return OllamaEmbeddings(
            model=config.OLLAMA_EMBEDDING_MODEL,
            base_url=config.OLLAMA_EMBEDDING_BASE_URL,
            keep_alive=0,
            num_gpu=config.OLLAMA_EMBEDDING_NUM_GPU,
        )
    if config.EMBEDDING_PROVIDER == "huggingface":
        return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    raise ValueError(f"Penyedia embedding tidak dikenal: {config.EMBEDDING_PROVIDER}")

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

def retrieve_materials(query: str, course_id: str = None, k: int = 3, material_ids: list[str] | None = None):
    """
    Retrieves the most relevant chunks for a given query and course.
    """
    if material_ids is not None and not material_ids:
        return []
    vectorstore = get_vectorstore()
    filter_dict = {"course_id": course_id} if course_id else None
    
    if material_ids is not None:
        allowed = {"material_id": {"$in": material_ids}}
        filter_dict = {"$and": [filter_dict, allowed]} if filter_dict else allowed
    results = vectorstore.similarity_search(
        query=query,
        k=k,
        filter=filter_dict
    )
    return results
