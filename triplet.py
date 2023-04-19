"""Make a Data / API / UI ticket triplet."""

import sys

import inquirer

import atl_util

ENV = atl_util.ENV

ACCEPT = "\n\n*Acceptance criteria:*\n  * \n  * \n  * "

jira = atl_util.jira()
PROJ = ENV["ATL_PROJECT"]
DRAFT = "DRAFT: TRANSIENT TICKET STATE"
empty = {
    "project": {"key": PROJ},
    "summary": DRAFT,
    "issuetype": {"name": "Story"},
}
STEPS = {
    "Data": {
        "summary": "DRAFT: {text[summary]} : Data",
        "description": "{text[description]}\n\n"
        "*Upstream data source*\n"
        "  * server: \n"
        "  * db: \n"
        "  * table/collection: \n"
        "  * fields/keys: \n\n"
        "*DataMart location*\n"
        "  * server: \n"
        "  * db: \n"
        "  * table/collection: \n"
        "  * fields/keys: \n",
        "labels": ["DATA", "NeedsDataInfo"],
    },
    "API": {
        "summary": "DRAFT: {text[summary]} : API",
        "description": "{text[description]}\n\n"
        "*DataMart*: see {tick[Data]}\n\n"
        "*API location*\n"
        "  * URI: \n",
        "labels": ["API", "NeedsAPIInfo"],
    },
    "UI": {
        "summary": "DRAFT: {text[summary]} : UI",
        "description": "{text[description]}\n\n"
        "*API*: see {tick[API]}\n\n"
        "*JSON contract*: \n\n"
        "*UI location*\n"
        "  * Tab: \n"
        "  * Table headers: \n"
        "  ** \n"
        "  *** filterable: y/n\n"
        "  *** sortable: y/n\n"
        "  *** pre-filtered: y/n\n"
        "  *** pre-sorted: y/n\n"
        "  ** \n"
        "  ** \n",
        "labels": ["UI"],
    },
}
existing = {k: v for k, v in zip(STEPS, map(int, sys.argv[1:] + [0] * len(STEPS)))}
steps = dict(i for i in STEPS.items() if existing[i[0]] != -1)
print(f"Creating / reusing tickets for these steps: {list(steps)}")
if "y" not in input("Ok [y/N]: ").lower():
    exit()

tick = {
    step: (
        f"{PROJ}-{existing[step]}"
        if existing[step] > 0
        else jira.issue_create(empty)["key"]
        if existing[step] == 0
        else "N/A"
    )
    for step in STEPS
}
# {'id': '49984',
#  'key': 'CE-3133',
#  'self': 'https://example.com/rest/api/2/issue/49984'}

text = inquirer.prompt(
    [
        inquirer.Text("summary", "Summary"),
        inquirer.Editor("description", "Description", default=ACCEPT),
    ]
)
text["summary"] = text["summary"].rstrip(".")

THIS = "this ticket"  # used in cross reference header


def description(summary, step, tick):
    text = f"h2. {summary} : {step}\n("
    sep = ""
    for step_i in STEPS:
        text += f"{sep}*{step_i}:* " + (
            THIS if step == step_i else f"{{tick[{step_i}]}}"
        )
        sep = " "
    text += ")\n\n"
    return text


for step, template in steps.items():
    if existing[step] != 0:
        continue
    jira.update_issue_field(
        tick[step],
        {
            "summary": template["summary"].format(text=text, tick=tick),
            "description": (
                description(text["summary"], step, tick) + template["description"]
            ).format(text=text, tick=tick),
            "labels": template["labels"],
        },
    )


extant = [i for i in STEPS if existing[i] != -1]
for step_i in range(1, len(extant)):
    link = {
        "type": {"name": "Blocks"},
        "inwardIssue": {"key": tick[extant[step_i - 1]]},
        "outwardIssue": {"key": tick[extant[step_i]]},
    }
    print(link)
    jira.create_issue_link(link)

for what in steps:
    print(f"{what} {ENV['ATL_HOST_JIRA']}/browse/{tick[what]}")
