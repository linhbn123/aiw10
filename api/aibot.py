def on_new_issue(new_issue):
    print(f"New issue: {new_issue}")
    return {'message': 'New issue'}


def on_new_pr(pr):
    print(f"New PR: {pr}")
    return {'message': 'New issue'}


def on_new_pr_commit(repo_path, pr_url, source_branch):
    print(f"New PR commit: {repo_path} {pr_url} {source_branch}")
    return {'message': 'New PR commit'}


def on_new_main_commit():
    print(f"New main commit")
    return {'message': 'New main commit'}


def on_new_pr_comment(pr_url, source_branch, comment):
    print(f"New PR comment: {pr_url} {source_branch} {comment}")
    return {'message': 'New PR comment'}


def on_new_pr_review(pr_url, source_branch, comments):
    print(f"New PR comment: {pr_url} {source_branch} {comment}")
    return {'message': 'New PR review'}


def scheduled_cleanup():
    return {'message': 'Scheduled cleanup'}
