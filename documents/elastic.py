from langchain_openai import OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from os import getenv
from elasticsearch import Elasticsearch


es_client = Elasticsearch(hosts=[f"{getenv('ES_SCHEMA')}://{getenv('ES_URL')}:{getenv('ES_PORT')}"])

embeddings = OpenAIEmbeddings(model='text-embedding-3-small')

vector_store = ElasticsearchStore(
    es_url=f"{getenv('ES_SCHEMA')}://{getenv('ES_URL')}:{getenv('ES_PORT')}",
    index_name=getenv('ES_INDEX', 'manthrabin'),
    embedding=embeddings,
    es_user=getenv('ES_USER'),
    es_password=getenv('ES_PASS'),
    es_params={"verify_certs": False}
)


def add_docs_pipeline(file_path: str, public_id: str):
    """Processes a PDF file, splits its content, and adds it to the vector store.

    Args:
        file_path (str): The path to the PDF file to be processed.
    """
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,       # Maximum size of each text chunk
        chunk_overlap=500,     # Overlap between chunks for context preservation
        length_function=len,   # Function to determine chunk length
        is_separator_regex=False,  # Whether the separator is a regex pattern
    )

    split_chunks = text_splitter.split_documents(docs)

    for chunk in split_chunks:
        chunk.metadata["public_id"] = public_id

    return vector_store.add_documents(documents=split_chunks)


def delete_docs_pipeline(public_id: str):
    es = vector_store.client
    body = {
        "query": {
            "term": { "metadata.public_id": public_id }
        }
    }
    return es.delete_by_query(index=getenv("ES_INDEX", "manthrabin"), body=body)
