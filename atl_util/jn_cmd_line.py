"""`jn` Jira Note quick actions command line.  See help()"""
import sys
import time

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()
project = ENV["ATL_PROJECT"]


def help():
    print(
        """\
jn -h
    Show this help
jn change the color for the third screen
    Find the nearest atlassian.env or .atlassian.env, working up the folder tree.
    Get ATL_PROJECT from there, as well as user, access token.
    Find the most recent ticket labeled To_Do.  Create a new one if not found or
    the most recent is In Review or Done.
    Append "(-) change the color for the third screen" to the description
jn -c Update the indexes.  Update indexes for all envs.
    Create a new ticket in ATL_PROJECT as above, summary = "Update the indexes",
    description = "Update the indexes for all envs."
jn -l term
    List 30 most recent tickets with text ~ "term".
    If term starts with ":", treat as jql instead.
jn -a 123 change the color for the third screen
    Append the todo text to issue 123 whether it's labeled To_Do or not."""
    )


def list_recent():
    query = f"project={project} "
    text = " ".join(sys.argv[1:])
    if text:
        if text.startswith(":"):
            query += " and " + text[1:]
        else:
            query += f' and text ~ "{text}"'
    query += " order by created desc"

    issues = jira.jql(query)
    issues = issues["issues"]
    for issue in issues[:30]:
        print(
            atl_util.jira_url(issue),
            issue["fields"]["issuetype"]["name"][0],
            issue["fields"]["summary"],
        )


def create():
    summary, description = map(str.strip, " ".join(sys.argv[1:]).split(".", 1))
    issue_key = jira.issue_create(
        {
            "project": {"key": ENV["ATL_PROJECT"]},
            "summary": summary,
            "issuetype": {"name": "Story"},
            "description": description,
        }
    )["key"]
    print(atl_util.jira_url(issue_key))


def todo(issue: dict = None):
    """Append a todo bullet item to a issue."""
    item = " ".join(sys.argv[1:])
    description = ""
    labels = []
    if issue is not None:
        # Use provided
        issue_key = issue["key"]
        description = issue["fields"]["description"] or ""
    else:
        # Look for open to do issue, must be most recent
        issues = jira.jql(f"project={project} and labels=To_Do order by created desc")[
            "issues"
        ]
        if issues and issues[0]["fields"]["status"]["name"] not in (
            "Done",
            "In Review",
        ):
            # Use open issue
            issue_key = issues[0]["key"]
            description = issues[0]["fields"]["description"] or ""
            labels = issues[0]["fields"]["labels"] or []
        else:
            # Create new to do issue
            summary = "Misc. To Do " + time.strftime("%Y-%m-%d")
            issue_key = jira.issue_create(
                {
                    "project": {"key": ENV["ATL_PROJECT"]},
                    "summary": summary,
                    "issuetype": {"name": "Story"},
                    "description": description,
                }
            )["key"]

    # Add new todo item to description
    description += f"\n(-) {item}"
    updates = {"description": description}
    if issue is None and "To_Do" not in labels:
        # Add To_Do if we created issue just now
        updates["labels"] = [*labels, "To_Do"]
    jira.update_issue_field(issue_key, updates)
    print(atl_util.jira_url(issue_key))


def append_todo():
    """Append to do bullet to specified issue."""
    key = sys.argv.pop(1)
    try:
        key = int(key)
        key = f"{project}-{key}"
    except ValueError:
        pass
    todo(jira.issue(key))


DISPATCH = {
    "-a": append_todo,
    "-c": create,
    "-h": help,
    "-l": list_recent,
    "todo": todo,
}

if __name__ == "__main__":
    mode = sys.argv.pop(1) if sys.argv[1].startswith("-") else "todo"
    DISPATCH[mode]()
