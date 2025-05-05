# Load DB chroma_slack_db and retrieve the most relevant documents for a given query

from langchain_chroma.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


def load_db():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectordb = Chroma(collection_name="slack_social_history", persist_directory="./chroma_slack_db", embedding_function=embeddings)
    return vectordb

def retrieve(query: str, k: int = 1) -> list[Document]:
    vectordb = load_db()
    docs = vectordb.similarity_search(query, k=k)
    output = ""
    for doc in docs:
        output += doc.page_content + "\n"
        output += f"Link: {doc.metadata['permalink_to_message']}\n"
    return output

if __name__ == "__main__":
    retrieve("Unit testing")
