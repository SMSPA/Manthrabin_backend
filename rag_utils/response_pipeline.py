"""
This script sets up a Retrieval-Augmented Generation (RAG) workflow combining OpenAI’s language models 
with Elasticsearch for document retrieval. It retrieves relevant documents from a vector store 
and feeds them into a prompt for answer generation.

Main workflow:
1. Load configuration settings from a .env file.
2. Set up OpenAI embeddings for vectorizing text.
3. Connect to Elasticsearch as the vector database.
4. Build a retriever for fetching relevant documents using vector similarity.
5. Define a prompt template for the AI model’s response.
6. Create two main interface functions:
   - `invoke(...)` for synchronous Q&A.
   - `stream(...)` for streamed response generation with sources.
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .web_search import  fetch_links_content


# Step 1: Load environment variables (e.g., API keys, URLs)
load_dotenv()


# Step 2: Initialize text embedding model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


# Step 3: Configure connection to Elasticsearch for storing and retrieving vector data
vector_store = ElasticsearchStore(
    es_url=os.getenv("ES_SCHEMA")+"://"+os.getenv("ES_URL")+":"+os.getenv("ES_PORT"),
    index_name=os.getenv("ES_INDEX"),
    embedding=embeddings,
    es_user=os.getenv("ES_USER"),
    es_password=os.getenv("ES_PASS"),
    es_params={"verify_certs": False}  # Useful for local/dev environments
)
es = Elasticsearch(
    hosts=["http://localhost:9200"]  # replace with your server's URL if not localhost
)

# Step 4: Define logic for retrieving related documents using similarity search
def _similarity_search(question: str) -> Dict[str, Any]:
    """
    Fetch documents from Elasticsearch that are similar to the input query.

    Returns:
        - 'context': Text combined from top-matching results
        - 'chunks': Metadata and scores for each retrieved segment
    """
    try:
        if not es.indices.exists(index="manthrabin"):
            print("Index 'manthrabin' does not exist. Creating index.")
            es.indices.create(index="manthrabin")
        results = vector_store.similarity_search_with_score(query=question, k=10)
    except Exception as e:
        print(f"Error: {e}")
    retrieved_chunks = []
    for doc, score in results:
        retrieved_chunks.append({
            "ID": doc.metadata.get("public_id", ""),
            "Context": doc.page_content,
            "Reliability": score
        })

    # Assemble text to be used in the LLM prompt
    context_text = "\n\nRelated Chunks:\n"
    for i, (doc, _) in enumerate(results, 1):
        context_text += f"\nSource {i} – {doc.metadata.get('Title', '')}:\n{doc.page_content}"

    return {
        "context": context_text,
        "chunks": retrieved_chunks
    }


# Wrap retrieval logic for use in LangChain pipelines
retriever = RunnableLambda(lambda inputs: _similarity_search(inputs["question"]))


# Step 5: Set up the instruction template used to guide AI-generated answers
system_prompt = (
    "You are an intelligent assistant. Use the retrieved content and any given user preferences "
    "to answer the question. If the context does not include the answer, respond with “I don't know.” "
    "Keep answers brief and informative (max three sentences). "
    "Account for these user preferences: {user_favorites}."
)

prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder("chat_history"),
    ("system", system_prompt),
    ("human",
     "The following instruction includes helpful context. Please complete the request accordingly.\n\n"
     "### Instruction: {context}\n\n"
     "### Web links: {link_data}"
     "### Input: {question}\n\n"
     "### Response:")
])


# Utility: Format raw conversation history into LLM-compatible message objects
def _reformat_history(history: List[Dict[str, str]]) -> List[BaseMessage]:
    """
    Convert a list of role-message dictionaries into LangChain-compatible message objects.
    """
    user_role = os.getenv("USER_ROLE", "user").lower()
    formatted = []

    for item in history:
        role = item.get("Role", "").lower()
        message = item.get("Message", "")
        formatted.append(HumanMessage(content=message) if role == user_role else AIMessage(content=message))

    return formatted


# Utility: Convert link data into a formatted string block
def _reformat_link_data(data: dict) -> str:
    output = "\nFetched link data:\n"
    for entry in data:
        if 'error' not in entry:
            output += f"\nSource {entry['Link']} \n–{entry['Content']}"
    return output


# Step 6a: Synchronous query-answer interface
def invoke(
    query: str,
    history: List[Dict[str, str]],
    favorites: List[str],
    model_name: str
) -> Dict[str, Any]:
    """
    Handle a single query through RAG: retrieve related content and generate a full response.

    Returns:
        - 'response': The generated text answer
        - 'sourcePoints': List of source document segments
    """
    # Retrieve relevant text and supporting metadata
    retrieval = _similarity_search(query)
    formatted_history = _reformat_history(history)
    web_links = fetch_links_content(query)

    prompt_inputs = {
        "context": retrieval["context"],
        "question": query,
        "link_data": _reformat_link_data(web_links),
        "chat_history": formatted_history,
        "user_favorites": ", ".join(favorites) if favorites else ""
    }

    model = ChatOpenAI(model=model_name)
    answer = model.invoke(prompt.invoke(prompt_inputs)).content

    return {
        "response": answer,
        "sourcePoints": retrieval["chunks"],
        "links_data": web_links
    }


# Step 6b: Streaming interface for real-time response generation
def stream(
    query: str,
    history: List[Dict[str, str]],
    favorites: List[str],
    model_name: str
):
    """
    Generate and stream the AI response in parts. Yield final source metadata after completion.

    Yields:
        - {'type': 'chunk', 'response': '...'} for each streamed token group
        - {'type': 'source', 'sourcePoints': [...]} once streaming ends
    """
    retrieval = _similarity_search(query)
    formatted_history = _reformat_history(history)
    web_links = fetch_links_content(query)

    prompt_inputs = {
        "context": retrieval["context"],
        "question": query,
        "link_data": _reformat_link_data(web_links),
        "chat_history": formatted_history,
        "user_favorites": ", ".join(favorites) if favorites else ""
    }

    model = ChatOpenAI(model=model_name, streaming=True)

    for output in model.stream(prompt.invoke(prompt_inputs)):
        yield {"type": "chunk", "response": output.content}

    yield {
        "type": "source",
        "sourcePoints": retrieval["chunks"],
        "links_data": web_links
    }


# For debugging or standalone testing
if __name__ == "__main__":
    example_history = [
        {"Role": "user", "Message": "What is Elasticsearch used for?"},
        {"Role": "assistant", "Message": "Elasticsearch is used for full-text search and analytics."},
    ]

    example_query = "Explain how vector search operates in Elasticsearch. https://laravel-livewire.com/"
    preferences = ["medical research", "AI applications"]

    # Run standard invocation
    result = invoke(example_query, example_history, preferences, model_name="gpt-4o-mini-search-preview-2025-03-11")
    print("Response:\n", result["response"])
    print("\nSources:")
    for item in result["sourcePoints"]:
        print(f"- {item['ID']}: {item['Context'][:100]}...")
    for src in result["links_data"]:
        print(f"• {src['Link']}: {src['Content'][:100]}...")

    # Run streaming version
    print("\nStreaming Output:")
    for chunk in stream(example_query, example_history, preferences, model_name="gpt-4o-mini"):  # gpt-4o-mini-search-preview-2025-03-11 for search
        if chunk["type"] == "chunk":
            print(chunk["response"], end="", flush=True)
        elif chunk["type"] == "source":
            print("\n\nRetrieved Sources:")
            for src in chunk["sourcePoints"]:
                print(f"• {src['ID']}: {src['Context'][:100]}...")
            for src in chunk["links_data"]:
                print(f"• {src['Link']}: {src['Content'][:100]}...")
