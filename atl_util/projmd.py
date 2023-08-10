"""JSON to markdown for project plan.

Currently JSON comes from Jira tickets via projjson.py, but there could be a
projjson_gh.py that reads from GitHub Issues instead.
"""
import json
from sys import stderr

import atl_util


def issue_deliv_url(data):
    """Get YAML deliverable info., and url, for each issue."""
    for epic in data["issues"]:
        deliv = next((i for i in epic["yamls"] if i["type"] == "deliverable"), None)
        if not deliv:
            print(f"Missing deliverable for {epic['key']}", file=stderr)
            continue
        url = atl_util.jira_url(epic["key"])
        yield epic, deliv, url


data = json.load(open("proj.json"))
sorting = list(issue_deliv_url(data))
sorting = [i for i in sorting if i[1].get("in_budget", True)]
# Sort by timing for all outputs
sorting.sort(key=lambda x: x[1].get("timing", "Q0"))
text = []
text.append(f"# Project Plan {data['generated']}\n")

# Long form list of deliverables
for epic, deliv, url in sorting:
    text += [
        f"* [{epic['key']}]({url}) {epic['summary']}  ",
        f"  {deliv['purpose']}  ",
        f"  {deliv['history']}  ",
    ]

# Cost estimates table
text += ["", "|Epic|API (weeks)|UI (weeks)|", "|---|---|---|"]
beans = {
    "api": {"total": 0, "k": 0.5},
    "ui": {"total": 0, "k": 0.75},
}
for epic, deliv, url in sorting:
    row = [""]
    row.append(f"[{epic['key']}]({url}) {epic['summary']}")
    for team in "api", "ui":
        req = beans[team]["k"] * sum(deliv["weeks"][team]) / 2
        beans[team]["total"] += req
        row.append(f"{req:.1f}")
    row.append("")
    text.append("|".join(row))
text.append(f"||{beans['api']['total']:.1f}|{beans['ui']['total']:.1f}|")

# Timeline table
text += ["", "|Item|Delivery|", "|---|---|"]
for epic, deliv, url in sorting:
    timeline = deliv.get("timing", "Q0")
    if len(timeline) > 2:  # Q23 -> Q2-3
        timeline = f"{timeline[:2]}-{timeline[2:]}"
    text.append(
        "|".join(["", f"[{epic['key']}]({url}) {epic['summary']}", timeline, ""])
    )

print("\n".join(text))
