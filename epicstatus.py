"""Analyze epic ticketing status."""
from collections import defaultdict
from pathlib import Path

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

query = (
    f"project = {atl_util.ENV['ATL_PROJECT']} "
    "and type = Epic and updated > startOfYear() "
    "and labels=CCD_FY23 "
)
todo = atl_util.jql_result(jira, query, use_default=True)

results = []
graph = {}
for epic in todo:
    issues = atl_util.partial(jira.epic_issues, epic["key"])
    issues = atl_util.fetch(issues)
    issues = list(issues)
    status = defaultdict(lambda: 0)
    atl_util.graph_add(graph, epic)
    done = set()
    for issue in issues:
        status[issue["fields"]["status"]["name"]] += 1
        for link in issue["fields"]["issuelinks"]:
            if link["type"]["name"] == "Blocks" and "outwardIssue" in link:
                atl_util.graph_add(graph, issue, link["outwardIssue"])
                done.add(link["outwardIssue"]["key"])
    for issue in issues:
        if issue["key"] not in done:
            atl_util.graph_add(graph, epic, issue)
        else:
            atl_util.graph_add(graph, issue)  # Ensure full version seen
    status = dict(sorted(status.items()))
    epic["_status"] = status
    results.append(epic)

results.sort(key=lambda x: x["fields"]["status"]["name"])
for epic in results:
    print(epic["key"], epic["fields"]["status"]["name"], epic["fields"]["summary"])
    if epic["_status"]:
        print("   ", epic["_status"])
Path("graph.dot").write_text(
    atl_util.graph_to_dot(graph, show_labels=["API", "Data", "DATA", "UI"])
)
