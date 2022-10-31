import atl_util

jira = atl_util.jira()

to_tag = atl_util.ENV["ATL_TO_TAG"].split()
add_tag = atl_util.ENV["ATL_ADD_TAG"]

for key in to_tag:

    issue = jira.issue(key)
    if add_tag not in issue["fields"]["labels"]:
        issue["fields"]["labels"].append(add_tag)
    jira.update_issue_field(key, {"labels": issue["fields"]["labels"]})
