import requests
import os

def fetch_linked_issues():
  # The GitHub personal access token
  headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}

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
      "owner": os.getenv('REPO_OWNER'),
      "name": os.getenv('REPO_NAME'),
      "number": int(os.getenv('PR_NUMBER'))
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


def link_issue_to_pull_request():
    # The GitHub personal access token
    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}

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
            "pullRequestId": os.getenv('PR_ID'),
            "body": f"Linking issue #{os.getenv('ISSUE_NUMBER')}"
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
