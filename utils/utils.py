import os
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.string import StrOutputParser

def construct_review_prompt(diffs, linked_issues):

    # Combine the changes into a string with clear delineation.

    combined_diffs = "\n".join([
        f"File: {file['filename']}\nDiff: \n{file['patch']}\n"
        for file in diffs
    ])+"\n\n"

    # Combine all linked issues
    combined_linked_issues = "\n".join(linked_issues)+"\n\n"

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        "Check the provided code changes against the requirements in the issues.\n"
        "Provide your feedback in Markdown format. Your feedback should include the following sections:\n"
        "## Overview of the changes\n"
        "In this section, you highlight the main changes using no more than 3 sentences for each change. "
        "Do not list changes by source code files. Instead, list changes across files.\n"
        "## How the changes address the issues\n"
        "In this section, for each issues which might be closed by the code changes, "
        "explain how the changes address that issue. "
        "Keep the text concise and straight to the point. "
        "If there is only 1 issue which might be closed by the code changes, do not mention or link to that issue.\n"
        "## Grading\n"
        "In this section, you give a score from 0 to 10 for the code changes. "
        "10 means the changes have fulfilled all requirements, and the code is good. "
        "0 means the changes are absolute garbage. "
        "If the source code files are all under directory 'tools' or '.github' directly or indirectly, "
        "or if the linked issues do not explicitly require testing, "
        "then lacking testing is not a reason to grade down\n"
        "-------------------------------------------------------------------------------------\n"
        "Code changes:\n"
        f"{combined_diffs}\n"
        "-------------------------------------------------------------------------------------\n"
        "Issues which might be closed by the code changes:\n"
        f"{combined_linked_issues}\n"
        "-------------------------------------------------------------------------------------\n"
    )
    return prompt

def construct_suggestion_prompt(diffs):

    # Combine the changes into a string with clear delineation.

    combined_diffs = "\n".join([
        f"File: {file['filename']}\nDiff: \n{file['patch']}\n"
        for file in diffs
    ])+"\n\n"

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        "Check the provided code changes and suggest how they can be improved.\n"
        "Provide your feedback in Markdown format. Your feedback should include the following sections:\n"
        "## Improvement suggestions\n"
        "In this section, you suggest a few ideas to improve the quality of the code. "
        "Be specific - do not just suggest generic improvements\n"
        "-------------------------------------------------------------------------------------\n"
        "Code changes:\n"
        f"{combined_diffs}\n"
    )
    return prompt

def call_openai(prompt):
    client = ChatOpenAI(api_key = os.getenv("OPENAI_API_KEY"), model="gpt-3.5-turbo")
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
