from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.string import StrOutputParser
from app.api import env


def call_openai(prompt):
    client = ChatOpenAI(api_key = env.OPENAI_API_KEY, model="gpt-4o")
    messages = [
        {"role": "system", "content": "You are a highly skilled engineer and your job is to review pull requests"},
        {"role": "user", "content": prompt}
    ]
    try:
        response = client.invoke(input=messages)
        parser = StrOutputParser()
        content = parser.invoke(input=response)
        return content
    except Exception as e:
        return f"An error occurred: {e}"
