from pinecone import Pinecone, ServerlessSpec
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

    # Initialize Pinecone
    pinecone = Pinecone(api_key=env.PINECONE_API_KEY)

    # Querying the vector database for "relevant" docs
    document_vectorstore = PineconeVectorStore(index=pinecone.Index(index_name), embedding=embeddings)
    retriever = document_vectorstore.as_retriever()
    context = retriever.invoke(combined_linked_issues)
    results = [
        f"Source: {doc.metadata['source']}\nContent: {doc.page_content}"
        for doc in context
    ]
    return results


def create_index_if_not_exists(index_name):
    # Create a new Pinecone instance
    pinecone = Pinecone(
        api_key=env.PINECONE_API_KEY
    )

    # Check if the index already exists
    if index_name not in pinecone.list_indexes().names():
        # Define the index configuration
        pinecone.create_index(
            name=index_name, 
            dimension=3072,  # For text-embedding-3-large
            metric='cosine',  # Similarity metric
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1' # The only available region for free plan
            )
        )

    print(f"Index '{index_name}' is created and ready to use.")
