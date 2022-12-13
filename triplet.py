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
steps = "data", "api", "ui"
existing = {k: v for k, v in zip((steps), map(int, sys.argv[1:] + [0, 0, 0]))}
tick = {
    step: (
        f"{PROJ}-{existing[step]}"
        if existing[step]
        else jira.issue_create(empty)["key"]
    )
    for step in steps
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


def description(summary, data, api, ui):
    what = "Data" if data == THIS else "API" if api == THIS else "UI"
    return f"h2. {summary} : {what}\n(*Data:* {data} *API:* {api} *UI:* {ui})\n\n"


if not existing["data"]:
    jira.update_issue_field(
        tick["data"],
        {
            "summary": f"DRAFT: {text['summary']} : Data",
            "description": description(text["summary"], THIS, tick["api"], tick["ui"])
            + f"{text['description']}\n\n"
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
            "labels": ["Data", "NeedsDataInfo"],
        },
    )

if not existing["api"]:
    jira.update_issue_field(
        tick["api"],
        {
            "summary": f"DRAFT: {text['summary']} : API",
            "description": description(text["summary"], tick["data"], THIS, tick["ui"])
            + f"{text['description']}\n\n"
            f"*DataMart*: see {tick['data']}\n\n"
            "*API location*\n"
            "  * URI: \n",
            "labels": ["API", "NeedsAPIInfo"],
        },
    )

if not existing["ui"]:
    jira.update_issue_field(
        tick["ui"],
        {
            "summary": f"DRAFT: {text['summary']} : UI",
            "description": description(text["summary"], tick["data"], tick["api"], THIS)
            + f"{text['description']}\n\n"
            f"*API*: see {tick['api']}\n\n"
            f"*JSON contract*: \n\n"
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
    )
link = {
    "type": {"name": "Blocks"},
    "inwardIssue": {"key": tick["data"]},
    "outwardIssue": {"key": tick["api"]},
}
jira.create_issue_link(link)
link = {
    "type": {"name": "Blocks"},
    "inwardIssue": {"key": tick["api"]},
    "outwardIssue": {"key": tick["ui"]},
}
jira.create_issue_link(link)

for what in steps:
    print(f"{what} {ENV['ATL_HOST_JIRA']}/browse/{tick[what]}")
