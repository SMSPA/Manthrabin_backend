"""
This module generates a concise, memorable chat name based on conversation history using OpenAI’s language model.

The overall workflow:
1. Loads environment variables from a .env file.
2. Initializes the OpenAI chat model (GPT-4o-mini).
3. Defines a structured system prompt that instructs the model to create a chat name.
4. Creates a prompt template combining chat history and system instructions.
5. Exposes a function:
   - `chat_name(history, user_favorites=None)`: Returns a generated chat name or “I don’t know.”
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# 1. Load environment variables from a .env file
load_dotenv()

# 2. Initialize the OpenAI chat model (GPT-4o-mini)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_tokens=50)

# 3. Define a structured system prompt for generating a chat name.
system_prompt = (
    "You are a helpful assistant whose job is to generate a short, memorable chat name "
    "based on the provided conversation history. Follow these rules:\n"
    "  • Only use the messages in chat_history; do not add any new context.\n"
    "  • Incorporate any user preferences or favorites if provided (user_favorites).\n"
    "  • If you cannot derive an appropriate name from the conversation, reply with “I don’t know.”\n"
    "  • Keep the chat name to a maximum of four words, each capitalized like a title "
    "(e.g., “Geo Search Explorer”)."
)

# 4. Create a prompt template that injects chat history and user preferences.
prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder("chat_history"),
    ("system", system_prompt),
    ("human", "Based on the above, generate a concise chat name:")
])

# Combine the template with the LLM into a single chain
chain = prompt | llm

def _reformat_history(
    history: List[dict], user_role_env: str = "USER_ROLE"
) -> List[BaseMessage]:
    """
    Converts a list of message dicts into LangChain BaseMessage objects.

    Each history entry should be a dict:
      {"Role": "user" or "assistant", "Message": "<text>"}

    The environment variable USER_ROLE (default key "USER_ROLE") defines how to detect user messages.
    """
    user_role = os.getenv(user_role_env, "user")
    conversation_messages: List[BaseMessage] = []

    for msg in history:
        role = msg.get("Role", "").lower()
        content = msg.get("Message", "")
        if role == user_role.lower():
            conversation_messages.append(HumanMessage(content=content))
        else:
            conversation_messages.append(AIMessage(content=content))

    return conversation_messages

def chat_name(
    history: List[dict], user_favorites: Optional[str] = None
) -> str:
    """
    Generates a chat name from conversation history.

    :param history: A list of dicts representing past messages:
                    [{"Role": "user", "Message": "..."}, {"Role": "assistant", "Message": "..."}]
    :param user_favorites: (Optional) A string of user preferences or favorites to influence naming.
    :return: The generated chat name, or “I don’t know.” if no suitable name can be derived.
    """
    # Reformat the raw history into BaseMessage objects
    conversation = _reformat_history(history)

    # If user_favorites is provided, prepend it as a hidden system remark
    if user_favorites:
        # Insert a system message that mentions preferences before the human instruction
        # We simulate this by adding one more system message at the front of chat_history
        pref_message = AIMessage(content=f"(User Favorites: {user_favorites})")
        conversation.insert(0, pref_message)

    # Invoke the chain with chat_history; the chain prompt already includes system instructions
    response = chain.invoke({"chat_history": conversation})
    return response.content.strip()

if __name__ == "__main__":
    # Example usage when running this file directly
    sample_history = [
        {"Role": "user", "Message": "What is Elasticsearch used for?"},
        {"Role": "assistant", "Message": "Elasticsearch is used for full-text search and log analytics."},
    ]
    sample_favorites = "Likes technical terms, prefers short titles"

    name = chat_name(sample_history, user_favorites=sample_favorites)
    print(f"Generated Chat Name: {name}")