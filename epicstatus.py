"""Analyze epic ticketing status."""
import time
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
todo = atl_util.jql_result(jira, query)

results = []
graph = {}
table = []
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

    lines = epic["fields"]["description"].split("\n")
    lines = [i for i in lines if i.startswith("status:")] or ["status: "]
    table.append(
        (
            atl_util.jira_link(epic, target="_epic"),
            epic["fields"]["status"]["name"],
            epic["fields"]["summary"],
            lines[-1][len("status: ") :],
        )
    )

results.sort(key=lambda x: x["fields"]["status"]["name"])
for epic in results:
    print(epic["key"], epic["fields"]["status"]["name"], epic["fields"]["summary"])
    if epic["_status"]:
        print("   ", epic["_status"])
Path("graph.dot").write_text(
    atl_util.graph_to_dot(graph, show_labels=["API", "Data", "DATA", "UI"])
)

table.sort(key=lambda x: (x[1], x[0]))  # by status, then key
with open("table.html", "w") as out:
    out.write(atl_util.HEADER)
    out.write(
        "<table><tr><th>Epic</th><th>Status</th><th>Summary</th><th>Status</th></tr>"
    )
    for row in table:
        out.write("<tr><td class='nowrap'>" + "</td><td>".join(row) + "</td></tr>")
    out.write("</table>")
    out.write("<p>" + time.asctime() + "</p>")
    out.write(atl_util.FOOTER)
