import json
from pathlib import Path

from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

VECTOR_DB_DIR = "local-vector-db"
VECTOR_EMBEDDINGS_INDEX_NAME = "local-index"

def get_documents():
    with open("local-doc-db/videos.json", "r") as video_collection:
        documents = json.loads(video_collection.read())

    return documents

def get_embedding_engine(model="text-embedding-ada-002", **kwargs):
    return OpenAIEmbeddings(model=model, **kwargs)

def prep_documents_for_vector_storage(documents):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500, chunk_overlap=100, allowed_special="all"
    )

    text_chunks, metadatas = [], []

    for document in documents:
        doc_text, doc_metadata = document["text"], document["metadata"]
        chunked_doc_texts = text_splitter.split_text(doc_text)
        doc_metadatas = [doc_metadata] * len(chunked_doc_texts)
        text_chunks += chunked_doc_texts
        metadatas += doc_metadatas

    return text_chunks, metadatas

def create_and_save_vector_embeddings():
    documents = get_documents()
    text_chunks, metadatas = prep_documents_for_vector_storage(documents)

    embedding_engine = get_embedding_engine()
    
    files = Path(VECTOR_DB_DIR).glob(f"{VECTOR_EMBEDDINGS_INDEX_NAME}.*")
    if files:
        for file in files:
            file.unlink() # wipe out existing indexes

    index = FAISS.from_texts(
        texts=text_chunks, embedding=embedding_engine, metadatas=metadatas
    )

    index.save_local(folder_path=VECTOR_DB_DIR, index_name=VECTOR_EMBEDDINGS_INDEX_NAME)


# For now just store the vector embeddings locally
Path("local-vector-db").mkdir(exist_ok=True)

create_and_save_vector_embeddings()
