"""Analyze epic ticketing status."""
from collections import defaultdict

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

query = (
    f"project = {atl_util.ENV['ATL_PROJECT']} "
    "and type = Epic and updated > startOfYear() "
)
todo = atl_util.jql_result(jira, query)

results = []
for epic in todo:
    issues = atl_util.partial(jira.epic_issues, epic["key"])
    issues = atl_util.fetch(issues)
    issues = list(issues)
    status = defaultdict(lambda: 0)
    for issue in issues:
        status[issue["fields"]["status"]["name"]] += 1
    status = dict(sorted(status.items()))
    epic["_status"] = status
    results.append(epic)

results.sort(key=lambda x: x["fields"]["status"]["name"])
for epic in results:
    print(epic["key"], epic["fields"]["status"]["name"], epic["fields"]["summary"])
    if epic["_status"]:
        print("   ",  epic["_status"])
