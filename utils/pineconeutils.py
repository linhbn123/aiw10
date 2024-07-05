from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from utils.constants import *

def fetch_relevant_documents(linked_issues):
    # Combine all linked issues
    combined_linked_issues = "\n".join(linked_issues)+"\n\n"

    # Note: we must use the same embedding model that we used when uploading the docs
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # Querying the vector database for "relevant" docs
    document_vectorstore = PineconeVectorStore(index_name=PINECONE_INDEX, embedding=embeddings)
    retriever = document_vectorstore.as_retriever()
    context = retriever.get_relevant_documents(combined_linked_issues)
    results = [
        f"Source: {doc.metadata['source']}\nContent: {doc.page_content}"
        for doc in context
    ]
    return results
