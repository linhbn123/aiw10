from app.services.autocode import *
from app.services.review import *
from app.services.beautify import *
from app.services.upload import *
from app.services.coprogram import *


def on_new_issue(repo_path, issue_id, issue_number, issue_title, issue_body):
    # autocode, raise PR, link to the issue
    print(f"New issue: {repo_path} {issue_id} {issue_number}, {issue_title}, {issue_body}")
    implement_task(repo_path, issue_id, issue_number, issue_title, issue_body)
    return {'message': 'New PR has been raised'}


def on_new_pr_commits(repo_owner: str, repo_name: str, repo_path: str, pr_number: int, source_branch: str):
    # Review _then_ beautify code as per PEP8. Do not do it the other way around.
    # Goal: Only commits made by normal users trigger AI actions.
    print(f"New PR commit: {repo_owner} {repo_name} {repo_path} {pr_number} {source_branch}")
    review_code_changes(repo_owner, repo_name, repo_path, pr_number)
    beautify(repo_path, pr_number, source_branch)
    return {'message': 'New PR / new PR commits'}


def on_new_main_commit(repo_path: str):
    # FIXME Currently the code we have worked with only support pdf loader
    # See other loaders here, especially for code https://github.com/langchain-ai/langchain/discussions/19020
    print(f"New main commit: {repo_path}")
    upload(repo_path)
    return {'message': 'New main commit'}


def on_new_pr_comment(repo_path: str, pr_number: int, comment: str):
    print(f"New PR comment: {repo_path} {pr_number} {comment}")
    address_review_comments(repo_path, pr_number, [comment])
    return {'message': 'New PR comment'}


def on_new_pr_review(repo_path: str, pr_number: str, comments):
    print(f"New PR comments: {repo_path} {pr_number} {comments}")
    address_review_comments(repo_path, pr_number, comments)
    return {'message': 'New PR review'}


def scheduled_cleanup():
    return {'message': 'Scheduled cleanup'}
