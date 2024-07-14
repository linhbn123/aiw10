from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import tool
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders.text import TextLoader
from langsmith import traceable
from app.utils import constants, commonutils, pineconeutils


@tool
@traceable
def upload_python_source_code_to_pinecone(repo_path: str, local_repo_path: str):
    """
    Upload python source code to pinecone.
    
    Args:
        repo_path (str): The repository path, e.g. if the repository http url is https://github.com/foo/bar.git then the repository path is foo/bar.
        local_repo_path (str): The path to the local repository where we will clone the remote repository, e.g. /tmp/data.
    """
    index_name = commonutils.get_repo_identifier(repo_path)
    pineconeutils.create_index_if_not_exists(index_name)

    # Prep documents to be uploaded to the vector database (Pinecone)
    loader = DirectoryLoader(local_repo_path, glob="**/*.py", loader_cls=TextLoader)
    raw_docs = loader.load()

    # Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    documents = text_splitter.split_documents(raw_docs)
    print(f"Going to add {len(documents)} documents to Pinecone")

    # Choose the embedding model and vector store
    embedding = OpenAIEmbeddings(model=constants.EMBEDDING_MODEL)
    PineconeVectorStore.from_documents(documents, embedding, index_name=index_name)
    print("Loading to vectorstore done")
