"""Generate a markdown report of UAT results from JIRA tickets."""

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()


def summary_markdown(issue):
    """Return the summary markdown for a JIRA ticket."""
    return (
        f"\n**{issue['fields']['status']['name']}** "
        f"(*{issue['fields']['issuetype']['name']}*): "
        f"{issue['fields']['description']}\n"
    )


def header(issue, level):
    """Markdown header for an issue."""
    return f"\n{'#'*level} {issue['key']} - {issue['fields']['summary']}\n"


query = f"issueKey = {ENV['ATL_ISSUE_KEY']}"
epic = atl_util.jql_result(jira, query, use_default=True)[0]
print(header(epic, 1))
print(summary_markdown(epic))
for issue in jira.epic_issues(epic["key"])["issues"]:
    print(header(issue, 2))
    print(summary_markdown(issue))
    for sub in jira.jql_get_list_of_tickets(f"parent = {issue['key']}"):
        print(header(sub, 3))
        print(summary_markdown(sub))
