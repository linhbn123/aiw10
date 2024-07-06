import pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from app.utils import constants, commonutils
from app.api import env


def fetch_relevant_documents(repo_path, linked_issues):
    index_name = commonutils.get_repo_identifier(repo_path)
    create_index_if_not_exists(index_name)

    # Combine all linked issues
    combined_linked_issues = "\n".join(linked_issues)+"\n\n"

    # Note: we must use the same embedding model that we used when uploading the docs
    embeddings = OpenAIEmbeddings(model=constants.EMBEDDING_MODEL)

    # Querying the vector database for "relevant" docs
    document_vectorstore = PineconeVectorStore(index_name, embedding=embeddings)
    retriever = document_vectorstore.as_retriever()
    context = retriever.get_relevant_documents(combined_linked_issues)
    results = [
        f"Source: {doc.metadata['source']}\nContent: {doc.page_content}"
        for doc in context
    ]
    return results


def create_index_if_not_exists(index_name):
    # Initialize Pinecone
    pinecone.init(api_key=env.PINECONE_API_KEY, environment=constants.PINECONE_ENV)

    # Check if the index already exists
    if index_name not in pinecone.list_indexes():
        # Define the index configuration
        pinecone.create_index(
            name=index_name,
            dimension=128,
            metric='cosine',  # Similarity metric
            shards=1
        )

    print(f"Index '{index_name}' is created and ready to use.")
