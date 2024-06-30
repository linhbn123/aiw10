import json
import logging

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from app.api import env, aibot

app = Flask(__name__)
app.debug = True


@app.errorhandler(Exception)
def handle_generic_exception(e):
    logging.exception(e)
    error = {
        "code": 500,
        "name": 'Internal Server Error',
        "errors": str(e),
    }
    return app.response_class(response=json.dumps(error), status=500, mimetype='application/json')


@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    logging.exception(e)
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
            response = aibot.on_new_main_commit(repo_path)
        else:
            response = {'message': 'Commit not to main branch or ready pull request'}

    elif event == 'issues' and payload.get('action') == 'opened':
        # Handle new issue creation
        repo_path = payload.get('repository', {}).get('full_name', None)
        new_issue = payload.get('issue', {})
        issue_number = new_issue.get('number', None)
        issue_title = new_issue.get('title', None)
        issue_body = new_issue.get('body', None)
        response = aibot.on_new_issue(repo_path, issue_number, issue_title, issue_body)

    elif event == 'pull_request':
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        if action in ['opened', 'ready_for_review', 'synchronize']:
            if pr.get('state') == 'open' and not pr.get('draft', False):
                if pr.get('user', {}).get('login') != env.BOOT_USERNAME:
                    head = pr.get('head', {})
                    repo = head.get('repo', {})
                    repo_owner = repo.get('owner', {}).get('login', None)
                    repo_name = repo.get('name', None)
                    repo_path = repo.get('full_name', None)
                    pr_number = pr.get('number', None)
                    source_branch = head.get('ref', None)
                    response = aibot.on_new_pr_commits(repo_owner, repo_name, repo_path, pr_number, source_branch)
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
