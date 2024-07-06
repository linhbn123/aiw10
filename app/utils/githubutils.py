import requests
from github import Github, PullRequest
from app.api import env


def get_pr(repo_path, pr_number):
  # Initialize GitHub API with token
  g = Github(env.GITHUB_TOKEN)
  
  # Get the repo object
  repo = g.get_repo(repo_path)

  # Fetch pull request by number
  return repo.get_pull(pr_number)


def fetch_linked_issues(repo_owner: str, repo_name: str, pr_number: int):
  # The GitHub personal access token
  headers = {"Authorization": f"Bearer {env.GITHUB_TOKEN}"}

  # The GraphQL query
  query = """
  query($owner: String!, $name: String!, $number: Int!) {
    repository(owner: $owner, name: $name) {
      pullRequest(number: $number) {
        closingIssuesReferences(first: 10) {
          nodes {
            number
            title
            body
            url
          }
        }
      }
    }
  }
  """

  # Variables for the query
  variables = {
      "owner": repo_owner,
      "name": repo_name,
      "number": pr_number
  }

  # Make the request to the GitHub GraphQL API
  response = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=headers)

  # Parse the response
  data = response.json()

  # Extract the linked issues
  linked_issues = data['data']['repository']['pullRequest']['closingIssuesReferences']['nodes']

  results = [
      f"Issue: [{issue['number']}: {issue['title']}]({issue['url']})\nContent: {issue['body']}"
      for issue in linked_issues
  ]
  
  return results


# Unfortunately, when a review (not an individual comment) is posted, we receive individual events
# instead of a single event containing all review comments. E.g. if there are n comments in the review
# (including replies) then we receive n + 1 events, 1 pull_request_review and n pull_request_review_comment
# We therefore need to rely on the pull_request_review and then invoke github API to retrieve all comments
# for that review
def get_review_comments(repo_path, pr_number, review_id):
    pr = get_pr(repo_path, pr_number)

    # Get the specific review by ID
    review = pr.get_review(review_id)

    # Get all comments for the specific review
    review_comments = review.get_comments()

    # Collect detailed information about each comment
    comments_details = []
    for comment in review_comments:
        author = {
            'display_name': comment.user.name,
            'email': comment.user.email,
            'username': comment.user.login
        }
        file_path = comment.path
        diff_hunk = comment.diff_hunk
        content = comment.body

        # Get replies to the comment
        replies = get_replies(pr, comment.in_reply_to_id)

        comments_details.append({
            'author': author,
            'file_path': file_path,
            'diff_hunk': diff_hunk,
            'content': content,
            'replies': replies
        })

    return comments_details


def get_replies(repo_path, pr_number, in_reply_to_id):
    pr = get_pr(repo_path, pr_number)
    
    # Get replies to the comment
    return get_replies_from_pr(pr, in_reply_to_id)


def get_replies_from_pr(pr: PullRequest, in_reply_to_id: int):
    # Get replies to the comment
    replies = []
    should_continue = True
    current_reply_to_id = in_reply_to_id
    while (should_continue):
      should_continue = False
      for may_be_parent_comment in pr.get_issue_comments():
          if may_be_parent_comment.id == current_reply_to_id:
              replies.append({
                'author': {
                  'display_name': may_be_parent_comment.user.name,
                  'email': may_be_parent_comment.user.email,
                  'username': may_be_parent_comment.user.login
                },
                'file_path': may_be_parent_comment.path,
                'diff_hunk': may_be_parent_comment.diff_hunk,
                'content': may_be_parent_comment.body,
              })
              current_reply_to_id = may_be_parent_comment.in_reply_to_id
              should_continue = True
    replies.reverse()  # Reverse the order of replies

    return replies
