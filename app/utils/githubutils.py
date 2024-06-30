import requests
from github import Github
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
