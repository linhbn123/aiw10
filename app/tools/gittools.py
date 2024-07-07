import os
import subprocess
import git
import requests
from github import Github
from langchain.tools import tool
from langsmith import traceable
from app.api import env
from app.utils import commonutils, githubutils


@tool
@traceable
def generate_branch_name(issue_number: int) -> str:
    """
    Generate a git branch name given a git issue number.
    
    Args:
        issue_number (int): The GitHub issue number.
        
    Returns:
        str: The generated branch name.
    """
    timestamp = commonutils.get_formatted_current_timestamp()
    branch_name = f"autocode/github-issue-{issue_number}-{timestamp}"
    print(f"Generated branch name: {branch_name}")
    return branch_name


@tool
@traceable
def clone_repo(repo_path: str, local_repo_path: str):
    """
    Clone the repository to the local repo path if not already cloned.

    Args:
        repo_path (string): The repository path, e.g. owner/repo-name.
        local_repo_path (string): The path to the local repository where we will clone the remote repository, e.g. /tmp/data.
    """
    repo_url = f"https://{env.GITHUB_TOKEN}@github.com/{repo_path}.git"

    if not os.path.exists(local_repo_path):
        git.Repo.clone_from(repo_url, local_repo_path)
        print(f"Cloned repo from {repo_url} to {local_repo_path}")
    else:
        print(f"Repo already exists at {local_repo_path}")


@tool
@traceable
def switch_to_local_repo_path(local_repo_path: str):
    """
    Switch to the local repo path.

    Args:
        local_repo_path (string): The path to the local repository where we will clone the remote repository, e.g. /tmp/data.
    """
    try:
        # Change the current working directory to the specified directory
        os.chdir(local_repo_path)
        print(f"Switched to directory: {local_repo_path}")
    except Exception as e:
        print(f"Failed to switch to directory: {e}")


@tool
@traceable
def checkout_source_branch(source_branch: str):
    """
    Checkout the main branch, pull latest changes, then checkout the specific branch.

    Args:
        source_branch (string): The source branch of the pull request.
    """
    # Initialize the repository object
    repo = git.Repo(os.getcwd())

    # 1. Checkout the main branch
    repo.git.checkout('main')

    # 2. Pull the latest changes
    repo.git.pull()

    # 3. Checkout the specific branch
    repo.git.checkout(source_branch)
    print(f"Active branch: {repo.active_branch.name}")


@tool
@traceable
def get_files_from_pull_request(repo_path: str, pr_number: int):
    """
    Retrieve the list of files changed in a pull request.

    Args:
        repo_path (string): The repository path, e.g. owner/repo-name.
        pr_number (number): The pull request number, e.g. if the pull request url is https://github.com/owner/repo-name/pull/1234 then the pull request number is 1234.

    Returns:
        list: A list of filenames that have been changed in the pull request.
    """
    pr = githubutils.get_pr(repo_path, pr_number)

    # Get the diffs of the pull request
    return [file.filename for file in pr.get_files()]


@tool
@traceable
def run_autopep8(files):
    """
    Run autopep8 on a list of files.

    Args:
        files (list): A list of file paths to be formatted.
    """
    for file in files:
        subprocess.run(['autopep8', '--in-place', file])


@tool
@traceable
def has_changes():
    """
    Check if the repository has any changes.

    Returns:
        bool: True if the repository has changes, False otherwise.
    """
    repo = git.Repo(os.getcwd())
    print(f"Repo has changes: {repo.is_dirty()}")
    return repo.is_dirty()


@tool
@traceable
def commit_and_push(source_branch: str, commit_message: str):
    """
    Commit the changes and push to the remote branch.

    Args:
        source_branch (string): The source branch of the pull request.
        commit_message (str): The commit message.
    """

    repo = git.Repo(os.getcwd())
    print(f"Active branch: {repo.active_branch.name}")
    repo.git.add(update=True)
    repo.index.commit(commit_message)
    origin = repo.remote(name='origin')
    print(f"Pushing changes to remote branch '{source_branch}'")
    push_result = origin.push(refspec=f'{source_branch}:{source_branch}')
    print("Push result:")
    for push_info in push_result:
        print(f"  - Summary: {push_info.summary}")
        print(f"    Remote ref: {push_info.remote_ref}")
        print(f"    Local ref: {push_info.local_ref}")
        print(f"    Flags: {push_info.flags}")


@tool
@traceable
def create_branch_and_push(local_repo_path: str, branch_name: str, commit_message: str):
    """
    Create a new branch, add all changed files, and push to the remote origin.
    
    Args:
        local_repo_path (string): The path to the local directory storing the github repository.
        branch_name (str): The name of the new branch.
        commit_message (str): The commit message.
    """
    try:
        # Initialize the repository object
        repo = git.Repo(local_repo_path)

        # Create a new branch and checkout
        repo.git.checkout('-b', branch_name)
        print(f"Created and switched to new branch: {branch_name}")

        # Add all changed files
        repo.git.add(A=True)
        print("Added all changed files.")

        # Commit changes
        repo.index.commit(commit_message)
        print(f"Committed changes with message: {commit_message}")

        # Push the branch to remote
        origin = repo.remote(name='origin')
        origin.push(branch_name)
        print(f"Pushed branch {branch_name} to remote origin.")
    except Exception as e:
        print(f"An error occurred: {e}")


@tool
@traceable
def create_pull_request(repo_path: str, local_repo_path: str, source_branch: str, title: str, body: str):
    """
    Create a pull request targeting the main branch.
    
    Args:
        repo_path (string): The repository path, e.g. owner/repo-name.
        local_repo_path (string): The path to the local directory storing the github repository.
        source_branch (string): The source branch of the pull request.
        title (str): The title of the pull request.
        body (str): The body description of the pull request.
    """
    try:
        # Initialize GitHub API with token
        g = Github(env.GITHUB_TOKEN)

        # Get the repo object
        repo = g.get_repo(repo_path)

        # Get the current branch name
        branch_name = git.Repo(local_repo_path).active_branch.name

        # Create a pull request
        pr = repo.create_pull(title=title, body=body, head=branch_name, base=source_branch)
        print(f"Pull request created: {pr.html_url}")
    except Exception as e:
        print(f"An error occurred: {e}")



@tool
@traceable
def link_issue_to_pull_request(pr_number: int, issue_id: int):
    """
    Link the specified pull request to the specified issue.
    
    Args:
        pr_number (number): The pull request number.
        issue_id (number): The issue number.
    """
    # The GitHub personal access token
    headers = {"Authorization": f"Bearer {env.GITHUB_TOKEN}"}

    # The GraphQL mutation
    mutation = """
    mutation($input: AddPullRequestReviewInput!) {
      addPullRequestReview(input: $input) {
        pullRequestReview {
          pullRequest {
            closingIssuesReferences(first: 1) {
              nodes {
                number
                title
              }
            }
          }
        }
      }
    }
    """

    # Variables for the mutation
    variables = {
        "input": {
            "pullRequestId": pr_number,
            "body": f"Linking issue #{issue_id}"
        }
    }

    # Make the request to the GitHub GraphQL API
    response = requests.post('https://api.github.com/graphql', json={'query': mutation, 'variables': variables}, headers=headers)

    # Parse the response
    data = response.json()

    # Check for errors in the response
    if 'errors' in data:
        raise Exception(f"Error linking issue to pull request: {data['errors']}")

    # Extract the linked issue details
    linked_issue = data['data']['addPullRequestReview']['pullRequestReview']['pullRequest']['closingIssuesReferences']['nodes'][0]

    result = f"Issue: [{linked_issue['number']}: {linked_issue['title']}] linked successfully."

    return result
