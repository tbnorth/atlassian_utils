"""Put '(ticket details)" link at top of epic descriptions.

Just links to '"epic link" = myProj-123'.
"""
import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

query = f"project = {atl_util.ENV['ATL_PROJECT']} and type = Epic and labels = CCD_FY23"
todo = atl_util.jql_result(jira, query)

# test !~ foo is not supported in JQL, and description may be None
todo = [
    i for i in todo if "([ticket details|" not in (i["fields"]["description"] or "")
]

for epic in todo:
    link = f"{ENV['ATL_HOST_JIRA']}/issues/?jql=%22Epic%20Link%22%3D{epic['key']}"
    print(link)
    description = epic["fields"]["description"] or ""
    description = f"([ticket details|{link}])\n\n{description}"
    jira.update_issue_field(epic["key"], {"description": description})
