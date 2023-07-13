"""Put '(ticket details)" link at top of epic descriptions.

Just links to '"epic link" = myProj-123'.
"""
import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

query = f"project = {atl_util.ENV['ATL_PROJECT']} and type = Epic and labels = CCD_FY23"
todo = atl_util.jql_result(jira, query)

mode = "add"  # regular addition of link to top of description
# mode = "fix"  # remove old link and add new one, edit code below

# test !~ foo is not supported in JQL, and description may be None
filter = (lambda a, b: a in b) if mode == "fix" else (lambda a, b: a not in b)
todo = [
    i for i in todo if filter("([ticket details|", i["fields"]["description"] or "")
]
print(f"Found {len(todo)} epics to fix")
print("Continue? [y/N]")
if input() != "y":
    exit()

for epic in todo:
    if mode == "fix":
        description = epic["fields"]["description"] or ""
        description = description.replace("//ccte-jira", "//jira", 1)
        jira.update_issue_field(epic["key"], {"description": description})
        print(atl_util.jira_url(epic), "fixed")
        continue

    link = f"{ENV['ATL_HOST_JIRA']}/issues/?jql=%22Epic%20Link%22%3D{epic['key']}"
    print(link)
    description = epic["fields"]["description"] or ""
    description = f"([ticket details|{link}])\n\n{description}"
    jira.update_issue_field(epic["key"], {"description": description})
