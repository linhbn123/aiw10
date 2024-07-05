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
        ref = payload.get('ref', '')
        repo_path = f"{payload['repository']['owner']['login']}/{payload['repository']['name']}"
        commits = payload.get('commits', [])
        filtered_commits = [commit for commit in commits if commit['author']['username'] != env.BOOT_USERNAME]
        
        if not filtered_commits:
            return jsonify({'message': 'No relevant commits'})

        if ref == 'refs/heads/main':
            response = on_new_main_commit()
        elif 'pull_request' in payload:
            pr = payload['pull_request']
            if pr.get('state') == 'open' and pr.get('merged') == False:
                pr_url = pr.get('html_url', '')
                source_branch = pr.get('head', {}).get('ref', '')
                response = on_new_pr_commit(repo_path, pr_url, source_branch)
            else:
                response = {'message': 'Pull request is not ready'}
        else:
            response = {'message': 'Commit not to main branch or ready pull request'}
 
    elif event == 'issue_comment':
        # Handle comments for a ready pull request that start with /support and are not raised by the bot
        issue_comment = payload.get('comment', {})
        pr = payload.get('issue', {}).get('pull_request', None)
        if pr and issue_comment:
            comment_body = issue_comment.get('body', '')
            commenter_username = issue_comment.get('user', {}).get('login', '')
            pr_state = payload.get('issue', {}).get('state', '')
            pr_url = payload.get('issue', {}).get('pull_request', {}).get('html_url', '')
            source_branch = payload.get('issue', {}).get('pull_request', {}).get('head', {}).get('ref', '')
            
            if (comment_body.startswith('/support') and 
                commenter_username != env.BOOT_USERNAME and 
                pr_state == 'open'):
                response = on_new_pr_comment(pr_url, source_branch, payload)
            else:
                response = {'message': 'Comment does not meet criteria'}
        else:
            response = {'message': 'Not an issue comment on a pull request'}

    elif event == 'pull_request_review':
        # Process review comments
        review_comments = payload.get('review', {}).get('body', [])
        pr_url = payload.get('pull_request', {}).get('html_url', '')
        source_branch = payload.get('pull_request', {}).get('head', {}).get('ref', '')
        response = on_new_pr_review(pr_url, source_branch, review_comments)

    elif event == 'issues' and payload.get('action') == 'opened':
        # Handle new issue creation
        new_issue = payload.get('issue', {})
        response = on_new_issue(new_issue)

    elif event == 'pull_request':
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        if action in ['opened', 'ready_for_review']:
            if pr.get('state') == 'open' and not pr.get('draft', False):
                response = on_new_pr(pr)
            else:
                response = {'message': 'Pull request is not ready or is a draft'}
        else:
            response = {'message': 'Pull request action not handled'}

    else:
        response = {'message': 'Event not handled'}

    return jsonify(response)


if __name__ == "__main__":
    app.run()
