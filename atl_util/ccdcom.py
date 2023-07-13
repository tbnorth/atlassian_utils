"""Validate CCDCOM tickets
"""
# from pprint import pprint

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

query = f"project = {atl_util.ENV['ATL_PROJECT']} status = Working"
todo = atl_util.jql_result(jira, query)

working_status = "Backlog", "In Progress", "In Review"
errors = []
for issue in todo:
    print(issue["key"], issue["fields"]["summary"])
    clones = [
        i
        for i in issue["fields"]["issuelinks"]
        if i["type"]["inward"] == "is cloned by"
    ]
    # pprint(list(i["inwardIssue"]["key"] for i in clones))
    if clones:
        for clone in clones:
            ce_issue = jira.issue(clone["inwardIssue"]["key"])
            ce_status = ce_issue["fields"]["status"]["name"]
            if ce_status not in working_status:
                errors.append(
                    f"{atl_util.jira_url(issue)} is cloned to "
                    f"{atl_util.jira_url(ce_issue)} which has status {ce_status}"
                )
            print("Cloned to", atl_util.jira_url(ce_issue), ce_status)
            if "ClonedToCCD" not in ce_issue["fields"]["labels"]:
                print("ClonedToCCD not in labels, adding")
                ce_issue["fields"]["labels"].append("ClonedToCCD")
                jira.update_issue_field(
                    ce_issue["key"], {"labels": ce_issue["fields"]["labels"]}
                )
    else:
        errors.append(f"{atl_util.jira_url(issue)} is not cloned")
print("\n".join(errors))
