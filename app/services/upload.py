from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders.text import TextLoader
from app.utils import constants, commonutils, pineconeutils


def upload(repo_path):
    index_name = commonutils.get_repo_identifier(repo_path)
    pineconeutils.create_index_if_not_exists(index_name)

    # Prep documents to be uploaded to the vector database (Pinecone)
    loader = DirectoryLoader(repo_path, glob="**/*.py", loader_cls=TextLoader)
    raw_docs = loader.load()

    # Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    documents = text_splitter.split_documents(raw_docs)
    print(f"Going to add {len(documents)} documents to Pinecone")

    # Choose the embedding model and vector store
    embedding = OpenAIEmbeddings(model=constants.EMBEDDING_MODEL)
    vector_store = PineconeVectorStore.from_documents(documents, embedding)
    vector_store.index_name = index_name
    print("Loading to vectorstore done")
