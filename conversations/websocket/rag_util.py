from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from os import getenv
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
print("Key:", getenv("OPENROUTER_API_KEY"))

# Example of using it in a chain
template = """Your a Persian AI assistant how answer the question. Remember you must answer the question by Persian language

Question:
{question}

Answer:
"""

prompt = PromptTemplate(template=template, input_variables=["question"])


def simple_chat(
        user_prompt: str,
        sessionID: str,
        model: str = "google/gemini-2.0-flash-exp:free"
):
    llm = ChatOpenAI(
        openai_api_key=getenv("OPENROUTER_API_KEY"),
        openai_api_base=getenv("OPENROUTER_BASE_URL"),
        model_name=model,
    )

    chain = prompt | llm | StrOutputParser()

    return chain.stream(user_prompt)


