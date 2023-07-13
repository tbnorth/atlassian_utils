"""Generate a markdown report of UAT results from JIRA tickets."""
import time

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()


def summary_markdown(issue):
    """Return the summary markdown for a JIRA ticket."""
    return (
        f"\n**{issue['fields']['status']['name']}** "
        f"(*{issue['fields']['issuetype']['name']}*): "
        f"{issue['fields']['description'] or '(no description)'}\n"
    )


def header(issue, level):
    """Markdown header for an issue."""
    return f"\n{'#'*level} {issue['key']} - {issue['fields']['summary']}\n"


def comments_markdown(issue):
    """Markdown comments for an issue."""
    comments = [
        i["body"] for i in issue["fields"]["comment"]["comments"] if i["body"].strip()
    ]
    if not comments:
        return ""
    return "**Comment**: " + "\n\n**Comment**: ".join(comments)


print("Report automatically generated from JIRA tickets")
print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

query = f"issueKey = {ENV['ATL_ISSUE_KEY']}"
epic = atl_util.jql_result(jira, query, use_default=True)[0]
print(header(epic, 1))
print(summary_markdown(epic))
print(comments_markdown(epic))
for issue in jira.epic_issues(epic["key"])["issues"]:
    print(header(issue, 2))
    print(summary_markdown(issue))
    print(comments_markdown(issue))
    for sub in jira.jql_get_list_of_tickets(f"parent = {issue['key']}"):
        print(header(sub, 3))
        print(summary_markdown(sub))
        print(comments_markdown(sub))
