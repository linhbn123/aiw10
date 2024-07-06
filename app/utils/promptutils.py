from app.utils import commonutils


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


def construct_coprogram_prompt(repo_path: str, local_repo_path: str, pr_number: int, source_branch: str, diffs, comments):

    # Combine the changes into a string with clear delineation.

    combined_diffs = "\n".join([
        f"File: {file['filename']}\nDiff: \n{file['patch']}\n"
        for file in diffs
    ])+"\n\n"

    # Combine all comments
    combined_comments = commonutils.to_formatted_json_string(comments) + "\n\n"

    # Construct the prompt with clear instructions for the LLM.
    prompt = (
        "Address the below review comments.\n"
        "- If the comments ask you to make code changes, then you clone the repository "
        f"{repo_path} to local directory {local_repo_path}. "
        f"Then in that local directory,  checkout the source branch {source_branch} "
        f"of pull request number {pr_number}, make code changes as per the review comments, "
        "commit the change and push to the remote repository.\n"
        "- If the comments do not ask you to make code changes, answer them. Be clear and concise.\n"
        "-------------------------------------------------------------------------------------\n"
        "Review comments:\n"
        f"{combined_comments}\n"
        "-------------------------------------------------------------------------------------\n"
        "Code changes:\n"
        f"{combined_diffs}\n"
        "-------------------------------------------------------------------------------------\n"
    )
    return prompt
