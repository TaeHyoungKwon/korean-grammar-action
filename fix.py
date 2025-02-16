import os
import json
import html
import re

import requests
from github import Github
from whatthepatch import parse_patch


def fix(original):
    response = requests.get(
        'https://m.search.naver.com/p/csearch/ocontent/util/SpellerProxy',
        params=dict(passportKey="e59150cb92f83d6ec3e3c9dd0fa5be193dff7a0a", q=original, color_blindness=0)
    )
    print(response.json())
    return html.unescape(response.json()['message']['result']['notag_html'])


def comment_fix_suggestion(gh_token, repo_name, pr_number, target):
    g = Github(gh_token)
    pr = g.get_repo(repo_name).get_pull(pr_number)
    for file in pr.get_files():
        if target and not re.match(target, file.filename):
            continue
        for diff in parse_patch(file.patch):
            for change in diff.changes:
                fixed = fix(change.line)
                if not change.old and fixed != change.line:
                    pr.create_comment(
                        f"""```suggestion\n{fixed}\n```""",
                        pr.get_commits()[0],
                        file.filename,
                        None,
                        "RIGHT", change.new
                    )


if 'GITHUB_EVENT_PATH' in os.environ:
    with open(os.environ.get('GITHUB_EVENT_PATH')) as gh_event:
        json_data = json.load(gh_event)
        comment_fix_suggestion(
            os.environ.get('GITHUB_TOKEN'),
            json_data['pull_request']['base']['repo']['full_name'],
            json_data['number'],
            os.environ.get('INPUT_TARGET')
        )
