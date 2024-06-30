from app.services import autocode, review, beautify, upload


def on_new_issue(repo_path, issue_number, issue_title, issue_body):
    # Implement the task, raise a PR, link to the issue
    print(f"New issue: {repo_path} {issue_number}, {issue_title}, {issue_body}")
    autocode.implement_task(repo_path, issue_number, issue_title, issue_body)
    return {'message': 'New PR has been raised'}


def on_new_pr_commits(repo_owner: str, repo_name: str, repo_path: str, pr_number: int, source_branch: str):
    # Review _then_ beautify code as per PEP8. Do not do it the other way around.
    # Goal: Only commits made by normal users trigger AI actions.
    print(f"New PR commit: {repo_owner} {repo_name} {repo_path} {pr_number} {source_branch}")
    review.review_code_changes(repo_owner, repo_name, repo_path, pr_number)
    beautify.beautify(repo_path, pr_number, source_branch)
    return {'message': 'New PR / new PR commits'}


def on_new_main_commit(repo_path: str):
    print(f"New main commit: {repo_path}")
    upload.upload(repo_path)
    return {'message': 'New main commit'}
