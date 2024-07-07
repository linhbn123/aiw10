import json

from flask import Flask, jsonify, request, abort
from werkzeug.exceptions import HTTPException

from app.api import env
from app.api.aibot import *

app = Flask(__name__)
app.config['DEBUG'] = True


@app.errorhandler(Exception)
def handle_generic_exception(e):
    error = {
        "code": 500,
        "name": 'Internal Server Error',
        "errors": str(e),
    }
    return app.response_class(response=json.dumps(error), status=500, mimetype='application/json')


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "errors": e.description,
    })
    response.content_type = "application/json"
    return response


@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    event = request.headers.get('X-GitHub-Event')
    payload = request.json

    print(f"Received event: {event} with body {payload}")

    if event == 'push':
        ref = payload.get('ref', None)
        repo = payload.get('repository', {})
        repo_path = repo.get('full_name', None)

        if ref == 'refs/heads/main':
            response = on_new_main_commit(repo_path)
        elif 'pull_request' in payload:
            pr = payload.get('pull_request', {})
            if pr.get('state') == 'open' and pr.get('merged') == False:
                commits = payload.get('commits', [])
                if all(commit.get('author', {}).get('username', None) != env.BOOT_USERNAME for commit in commits):
                    repo_owner = repo.get('owner', {}).get('login', None)
                    repo_name = repo.get('name', None)
                    pr_number = pr.get('number', None)
                    source_branch = pr.get('head', {}).get('ref', None)
                    response = on_new_pr_commits(repo_owner, repo_name, repo_path, pr_number, source_branch)
                else:
                    response = {'message': 'Commit author is the bot, ignoring'}
            else:
                response = {'message': 'Pull request is not ready'}
        else:
            response = {'message': 'Commit not to main branch or ready pull request'}
 
    elif event == 'issue_comment':
        # Handle comments for a pull request that start with /support and are not raised by the bot
        issue_comment = payload.get('comment', {})
        pr = payload.get('issue', {}).get('pull_request', {})
        if pr and issue_comment:
            comment_body = issue_comment.get('body', None)
            commenter_username = issue_comment.get('user', {}).get('login', None)
            in_reply_to_id = issue_comment.get('in_reply_to_id', None)
            
            if (comment_body.startswith('/support') and 
                commenter_username != env.BOOT_USERNAME):
                pr_url = pr.get('html_url', '')
                pr_number = commonutils.extract_pr_number(pr_url)
                repo_path = payload.get('repository', {}).get('full_name', None)
                comment = {
                    'comment': comment_body,
                    'replies': githubutils.get_replies(repo_path, pr_number, in_reply_to_id)
                }
                response = on_new_pr_comment(repo_path, pr_number, comment)
            else:
                response = {'message': 'Comment does not meet criteria'}
        else:
            response = {'message': 'Not an issue comment on a pull request'}

    elif event == 'pull_request_review':
        # Process review comments
        review = payload.get('review', {})
        review_content = review.get('body', [])
        review_username = review.get('user', {}).get('login', None)
        if (review_content.startswith('/support') and 
            review_username != env.BOOT_USERNAME):
            repo_path = payload.get('repository', {}).get('full_name', None)
            pr = payload.get('issue', {}).get('pull_request', None)
            pr_number = pr.get('number', {})
            review_id = review.get('id', None)
            # Unfortunately, when a review (not an individual comment) is posted, we receive individual events
            # instead of a single event containing all review comments. E.g. if there are n comments in the review
            # (including replies) then we receive n + 1 events, 1 pull_request_review and n pull_request_review_comment
            # We therefore need to rely on the pull_request_review and then invoke github API to retrieve all comments
            # for that review
            review_comments = githubutils.get_review_comments(repo_path, pr_number, review_id)
            response = on_new_pr_review(repo_path, pr_number, review_comments)
        else:
            response = {'message': 'Review does not meet criteria'}

    elif event == 'issues' and payload.get('action') == 'opened':
        # Handle new issue creation
        new_issue = payload.get('issue', {})
        issue_number = new_issue.get('number', None)
        issue_title = new_issue.get('title', None)
        issue_body = new_issue.get('body', None)
        response = on_new_issue(issue_number, issue_title, issue_body)

    elif event == 'pull_request':
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        if action in ['opened', 'ready_for_review']:
            if pr.get('state') == 'open' and not pr.get('draft', False):
                if pr.get('user', {}).get('login') != env.BOOT_USERNAME:
                    head = pr.get('head', {})
                    repo = pr.get('repo', {})
                    repo_owner = repo.get('owner', {}).get('login', None)
                    repo_name = repo.get('name', None)
                    repo_path = repo.get('full_name', '')
                    pr_number = pr.get('number', {})
                    source_branch = head.get('ref', '')
                    response = on_new_pr_commits(repo_owner, repo_name, repo_path, pr_number, source_branch)
                else:
                    response = {'message': 'Pull request author is the bot, ignoring'}
            else:
                response = {'message': 'Pull request is not ready or is a draft'}
        else:
            response = {'message': 'Pull request action not handled'}

    else:
        response = {'message': 'Event not handled'}

    return jsonify(response)


if __name__ == "__main__":
    app.run()
