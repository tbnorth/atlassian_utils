"""`jn` Jira Note quick actions command line.  See help()."""
import sys
import time

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()
project = ENV["ATL_PROJECT"]


def help():
    """Show help."""
    print(
        """\
jn -h
    Show this help
jn
    Show most recent To_Do tickets.
jn change the color for the third screen
    Find the nearest atlassian.env or .atlassian.env, working up the folder tree.
    Get ATL_PROJECT from there, as well as user, access token.
    Find the most recent ticket labeled To_Do.  Create a new one if not found or
    the most recent is In Review or Done.
    Append "(-) change the color for the third screen" to the description
jn -n change the color for the third screen
    Create a new To_Do regardless of status of existing.
jn -c Update the indexes.  Update indexes for all envs.
    Create a new ticket in ATL_PROJECT as above, summary = "Update the indexes",
    description = "Update the indexes for all envs."
jn -l term
    List 30 most recent tickets with text ~ "term".
    If term starts with ":", treat as jql instead.
jn -a 123 change the color for the third screen
    Append the todo text to issue 123 whether it's labeled To_Do or not."""
    )


def find_recent(text):
    """Find recent issues matching expression."""
    query = f"project={project} "
    if isinstance(text, str):
        text = [text]  # Not always from sys.argv

    text = " ".join(text)
    if text:
        if text.startswith(":"):
            query += " and " + text[1:]
        else:
            query += f' and text ~ "{text}"'
    query += " order by updated desc"

    print(query)
    issues = jira.jql(query)
    return issues["issues"]


def list_recent():
    """Display recent issues matching user expression."""
    issues = find_recent(sys.argv[1] if sys.argv[1:] else [])
    display_issues(issues)


def show_latest():
    """Display recent To_Do tickets."""
    issues = find_recent(":labels=To_Do")
    display_issues(issues)


def display_issues(issues):
    """Display a list of issues."""
    for issue in issues[:30]:
        issue_type = issue["fields"]["issuetype"]["name"]
        print(
            atl_util.jira_url(issue),
            "t" if issue_type == "Sub-task" else issue_type[0],
            issue["fields"]["status"]["name"],
            issue["fields"]["summary"],
        )


def create():
    """Create a ticket."""
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


def new_todo():
    """Pass create new flag to todo()."""
    todo(create_new=True)


def todo(issue: dict = None, create_new=None):
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
        if (
            issues
            and issues[0]["fields"]["status"]["name"]
            not in (
                "Done",
                "In Review",
            )
            and create_new is not True
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
    description += f"\n(!) {item}"
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
    "-n": new_todo,
    "-c": create,
    "-h": help,
    "-l": list_recent,
    "todo": todo,
    "list": show_latest,
}

if __name__ == "__main__":
    if sys.argv[1:]:
        mode = sys.argv.pop(1) if sys.argv[1].startswith("-") else "todo"
    else:
        mode = "list"
    DISPATCH[mode]()
