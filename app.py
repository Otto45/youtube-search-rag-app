import os
import prompts

from langchain.chat_models import ChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import MongoDBAtlasVectorSearch
from pymongo import MongoClient

def get_embeddings():
    return BedrockEmbeddings()

def get_vector_store():
    client = MongoClient(os.environ["MONGODB_ATLAS_CLUSTER_URI"])

    db_name = "youtube_ai_search"
    collection_name = "video_transcripts"
    collection = client[db_name][collection_name]
    index_name = "video_transcripts_embeddings_index"
    embeddings = get_embeddings()

    return MongoDBAtlasVectorSearch(
        collection, embeddings, index_name=index_name
    )

# Main

user_prompt = input("Prompt: ")

vector_store = get_vector_store()
documents = vector_store.similarity_search(user_prompt)
llm = ChatOpenAI(model_name="gpt-4", temperature=0, max_tokens=256)

chain = load_qa_with_sources_chain(
    llm,
    chain_type="stuff",
    verbose=False,
    prompt=prompts.main,
    document_variable_name="sources",
)

result = chain(
    {"input_documents": documents, "question": user_prompt}, return_only_outputs=True
)

answer = result["output_text"]
print(answer)
