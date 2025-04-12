from langchain_openai import OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore
# from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from os import getenv
from dotenv import load_dotenv
from elasticsearch import Elasticsearch


load_dotenv()

es_client = Elasticsearch(hosts=[f"{getenv('ES_SCHEMA')}://{getenv('ES_URL')}:{getenv('ES_PORT')}"])

embeddings = OpenAIEmbeddings(model='text-embedding-3-small')

# Configure and initialize the Elasticsearch vector store
vector_store = ElasticsearchStore(
    es_url=f"{getenv('ES_SCHEMA')}://{getenv('ES_URL')}:{getenv('ES_PORT')}",
    index_name=getenv('ES_INDEX'),
    embedding=embeddings,
    # es_user=getenv('ES_USER'),
    # es_password=getenv('ES_PASS'),
    es_params={"verify_certs": False}  # Disable certificate verification for Elasticsearch
)


def add_docs_pipeline(file_path: str):
    """Processes a PDF file, splits its content, and adds it to the vector store.

    Args:
        file_path (str): The path to the PDF file to be processed.
    """
    # Load PDF document
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # Split document into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,       # Maximum size of each text chunk
        chunk_overlap=500,     # Overlap between chunks for context preservation
        length_function=len,   # Function to determine chunk length
        is_separator_regex=False,  # Whether the separator is a regex pattern
    )

    # Generate text chunks
    documents = text_splitter.split_documents(docs)

    # Store processed documents in Elasticsearch vector store
    return vector_store.add_documents(documents=documents)


def delete_docs_pipeline(uuids: list):
    """Deletes documents from the Elasticsearch vector store based on their UUIDs.

    Args:
        uuids (list): A list of document UUIDs to be deleted.

    Returns:
        dict: The response from the Elasticsearch delete operation.
    """
    return vector_store.delete(ids=uuids)
