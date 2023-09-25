import prompts
import vectordb

from langchain.chat_models import ChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain

user_prompt = input("Prompt:")

embedding_engine = vectordb.get_embedding_engine(allowed_special="all")
vector_index = vectordb.get_vector_index()

sources_and_scores = vector_index.similarity_search_with_score(user_prompt, k=3)
sources, scores = zip(*sources_and_scores)

llm = ChatOpenAI(model_name="gpt-4", temperature=0, max_tokens=256)
chain = load_qa_with_sources_chain(
    llm,
    chain_type="stuff",
    verbose=False,
    prompt=prompts.main,
    document_variable_name="sources",
)

result = chain(
    {"input_documents": sources, "question": user_prompt}, return_only_outputs=True
)

answer = result["output_text"]
print(answer)
