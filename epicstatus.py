"""Analyze epic ticketing status."""
import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

query = f"project = {atl_util.ENV['ATL_PROJECT']} and type = Epic and labels = CCD_FY23"
print(query)
todo = jira.jql_get_list_of_tickets(query)

for epic in todo:
    # print(jira.epic_issues(epic["key"]))
    issues = atl_util.partial(jira.epic_issues, epic["key"])
    issues = atl_util.fetch(issues)
    print([i['key'] for i in issues])
