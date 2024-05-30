"""JSON to markdown for project plan.

Currently JSON comes from Jira tickets via projjson.py, but there could be a
projjson_gh.py that reads from GitHub Issues instead.

docker run --rm -it -u `id -u`:`id -g` -v $PWD:/data \
    pandoc/latex /data/proj.md -o /data/proj.docx
"""
import json
from sys import stderr

import atl_util
from atl_util import ENV


def issue_deliv_url(data):
    """Get YAML deliverable info., and url, for each issue."""
    for epic in data["issues"]:
        deliv = next((i for i in epic["yamls"] if i["type"] == "deliverable"), None)
        if not deliv:
            print(f"Missing deliverable for {epic['key']}", file=stderr)
            # continue
        url = atl_util.jira_url(epic["key"])
        yield epic, deliv, url


data = json.load(open("proj.json"))
sorting = list(issue_deliv_url(data))
# sorting = [i for i in sorting if i[1].get("in_budget", True)]
# Sort by timing for all outputs
# sorting.sort(key=lambda x: x[1].get("timing", "Q0"))
text = []
text.append(f"# Project Plan {data['generated']}\n")
sep = ["  \n---\n  \n"]
text += sep

# Long form list of deliverables
for epic, deliv, url in sorting:
    purpose = deliv["purpose"] if deliv else ""
    history = deliv["history"] if deliv else ""
    description = "  \n".join((epic["description"] or "").replace("\r", "").split("\n"))
    text += [
        f"\n\n## [{epic['key']}]({url}) {epic['summary']}  ",
        f"  {purpose}  ",
        f"  {history}  ",
        f"\n\n{description}\n\n",
    ]
text += sep

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
        req = sum(deliv["weeks"][team]) if deliv else 0
        req = beans[team]["k"] * req / 2
        beans[team]["total"] += req
        row.append(f"{req:.1f}")
    row.append("")
    text.append("|".join(row))
text.append(f"||{beans['api']['total']:.1f}|{beans['ui']['total']:.1f}|")
text += sep

# Timeline table
text += ["", "|Item|Delivery|", "|---|---|"]
for epic, deliv, url in sorting:
    timeline = deliv.get("timing", "Q0") if deliv else "Q0"
    if len(timeline) > 2:  # Q23 -> Q2-3
        timeline = f"{timeline[:2]}-{timeline[2:]}"
    text.append(
        "|".join(["", f"[{epic['key']}]({url}) {epic['summary']}", timeline, ""])
    )
text += sep

# Cost calcs.
rate = int(ENV["ATL_CONTRACTOR_RATE"])
# api 0 ui 100 -> {"api": 0, "ui": 100}
prop = iter(ENV["ATL_CONTRACTOR_PROP"].split(" "))
prop = dict((i, float(next(prop))) for i in prop)
text += [f"Using the suggested ${rate}/hr for contractor budgeting:", ""]
for team in "api", "ui":
    name = team.upper()
    text += [f"\n{name}", ""]
    beans[team]["hours"] = int(beans[team]["total"] * 40 * prop[team] / 100)
    beans[team]["dollars"] = int(beans[team]["hours"] * rate)
    text += [
        f"{beans[team]['total']} \"100%\" "
        f"contractor weeks = {beans[team]['hours']} hours",
        "",
        f"{beans[team]['hours']} x ${rate:,} = ${beans[team]['dollars']:,}",
        "",
        "But this would be reduced proportional "
        f"to the level of Fed. {name} involvement.",
    ]
contract = beans["api"]["dollars"] + beans["ui"]["dollars"]
maint = int(contract * 0.2)
text += [
    "", "Total cost:", "",
    f"- Contractor cost: ${contract:.0f}",
    f"- Maintenance of existing code, updates, bug fixes etc. at 20%: ${maint:,}",
    f"- Total: ${contract + maint:,}",
    "- Fed. 40 hour weeks",
    f"  - API: 0-{beans['api']['total']} depending on contractor use",
    f"  - UI: 0-{beans['ui']['total']} depending on contractor use",
]


print("\n".join(text))
