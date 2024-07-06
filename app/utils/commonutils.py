import re
import json
from datetime import datetime


def get_repo_identifier(repo_path):
    return repo_path.replace('/', '-')


def get_formatted_current_timestamp():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def extract_pr_number(url: str) -> int:
    match = re.search(r'/pull/(\d+)', url)
    if match:
        return int(match.group(1))
    return None


def to_formatted_json_string(json_object):
    return json.dumps(json_object, indent=4)
