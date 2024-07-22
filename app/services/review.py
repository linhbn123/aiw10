from langchain.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI
from app.utils import constants, promptutils, openaiutils, pineconeutils, githubutils


def review_code_changes(repo_owner: str, repo_name: str, repo_path, pr_number):
    pr = githubutils.get_pr(repo_path, pr_number)

    # Get all comments on the pull request
    comments = pr.get_issue_comments()

    # Filter comments by the unique string and delete them
    for comment in comments:
        if constants.UNIQUE_STRING in comment.body:
            print(f"Deleting comment {comment.id} containing the unique string")
            comment.delete()

    linked_issues = githubutils.fetch_linked_issues(repo_owner, repo_name, pr_number)

    if len(linked_issues) == 0:
        comment = pr.create_issue_comment(f"{constants.UNIQUE_STRING}\nThere are no linked issues. Auto-review can't be done.")
        print("Comment created with ID:", comment.id)
        return

    # Get the diffs of the pull request
    diffs = [
        {
            "filename": file.filename,
            "patch": file.patch 
        } 
        for file in pr.get_files()
    ]

    # Format data for OpenAI prompt
    prompt = promptutils.construct_review_prompt(diffs, linked_issues)

    # Call OpenAI to generate the review
    generated_review = openaiutils.call_openai(prompt)

    # Get the relevant documents
    relevant_documents = pineconeutils.fetch_relevant_documents(repo_path, linked_issues)

    # Format data for OpenAI prompt
    query = promptutils.construct_suggestion_prompt(diffs)

    # Adding context to our prompt
    template = PromptTemplate(template="{query} Context: {context}", input_variables=["query", "context"])
    prompt_with_context = template.invoke({"query": query, "context": relevant_documents})

    # Asking the LLM for a response from our prompt with the provided context
    llm = ChatOpenAI(temperature=0.7)
    improvement_suggestions = llm.invoke(prompt_with_context)

    # Write a comment on the pull request
    comment = pr.create_issue_comment(f"{constants.UNIQUE_STRING}\n\n{generated_review}\n\n{improvement_suggestions.content}")
    print("Comment created with ID:", comment.id)
