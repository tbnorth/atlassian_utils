"""Make a Data / API / UI ticket triplet."""

import inquirer

import atl_util

ENV = atl_util.ENV

ACCEPT = "\n\n*Acceptance criteria:*\n  * \n  * \n  * "

jira = atl_util.jira()

empty = {
    "project": {"key": ENV["ATL_PROJECT"]},
    "summary": "TRANSIENT TICKET STATE",
    "issuetype": {"name": "Story"},
}
data = jira.issue_create(empty)["key"]
api = jira.issue_create(empty)["key"]
ui = jira.issue_create(empty)["key"]
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


jira.update_issue_field(
    data,
    {
        "summary": f"{text['summary']} : Data",
        "description": description(text["summary"], THIS, api, ui)
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
jira.update_issue_field(
    api,
    {
        "summary": f"{text['summary']} : API",
        "description": description(text["summary"], data, THIS, ui)
        + f"{text['description']}\n\n"
        f"*DataMart*: see {data}\n\n"
        "*API location*\n"
        "  * URI: \n",
        "labels": ["API", "NeedsAPIInfo"],
    },
)
jira.update_issue_field(
    ui,
    {
        "summary": f"{text['summary']} : UI",
        "description": description(text["summary"], data, api, THIS)
        + f"{text['description']}\n\n"
        f"*API*: see {api}\n\n"
        f"*JSON contract*: \n\n"
        "*UI location*\n"
        "  * Tab: \n"
        "  * Table headers: \n"
        "  ** \n"
        "  ** \n"
        "  ** \n",
        "labels": ["UI"],
    },
)
link = {
    "type": {"name": "Blocks"},
    "inwardIssue": {"key": data},
    "outwardIssue": {"key": api},
}
jira.create_issue_link(link)
link = {
    "type": {"name": "Blocks"},
    "inwardIssue": {"key": api},
    "outwardIssue": {"key": ui},
}
jira.create_issue_link(link)

for what in "data", "api", "ui":
    print(f"{what} {ENV['ATL_HOST_JIRA']}/browse/{locals()[what]}")
