"""Utilities for accessing Atlassian services."""
import html
import os
import re
import readline
import sys
import time
from collections import defaultdict, namedtuple
from collections.abc import Iterable
from functools import cache, partial
from itertools import chain
from pathlib import Path
# from pprint import pprint
from urllib.parse import urljoin

import atlassian
import requests
from dotenv import load_dotenv

assert partial  # imported for client convenience
HISTORY = ".history"
if Path(HISTORY).exists():
    readline.read_history_file(HISTORY)

EpicInfo = namedtuple("EpicInfo", "name link type")

load_dotenv("atlassian.env")
ENV = os.environ

STATUS_DONE = "Abandon", "Done"
EDGE_COLOR = {
    "Epic": "#6666bb",
}
EDGE_COLOR_DEFAULT = "#000000"
NODE_COLOR = {
    "Abandon": "#eeeeee",
    "Done": "#ffffff",
    "Epic": "#bbbbff",
    "Ice Box": "#aaaaaa",
    "In Review": "#eeddaa",
    "In Code Review": "#eeddaa",
    "In Progress": "#ffdddd",
}
NODE_COLOR_DEFAULT = "#ffaaaa"
NODE_SHAPE = {
    # "Ice Box": "ellipse",
    "Bug": "note",
}
NODE_SHAPE_DEFAULT = "box"

HEADER = """<!doctype html>
<html lang="en"><head><title>:Atlassian Report:</title>
<link rel="stylesheet"
href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css"
integrity="sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65"
crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.min.js"
integrity="sha384-cuYeSxntonz0PPNlHhBs68uyIAVpIIOZZ5JqeqvYYIcEL727kskC66kF92t6Xl2V"
crossorigin="anonymous"></script>
<style>.nowrap {white-space: nowrap;}</style>
</head><body>"""
FOOTER = "</body></html>"


def __make_connection(type_):
    """Function factory for Bitbucket / Confluence / Jira connection functions.
    Uses the Python API wrapper objects.
    """

    def func(url=None, username=None, password=None):
        """Return required connection type."""
        kwargs = {"url": url or ENV["ATL_HOST_" + type_.upper()]}
        auth = password or ENV.get("ATL_PASS_" + type_.upper()) or ENV["ATL_PASS"]
        if auth.startswith("token:"):
            kwargs.update({"token": auth[len("token:") :]})
        else:
            kwargs.update(
                {
                    "username": username or ENV["ATL_USER"],
                    "password": auth,
                }
            )

        return getattr(atlassian, type_)(**kwargs)

    func.__doc__ = f"Return a {type_} connection."
    return func


bitbucket = __make_connection("Bitbucket")
confluence = __make_connection("Confluence")
jira = __make_connection("Jira")


class APIWrapper:
    """Wrapper for direct (requests) access to API for things not covered by the
    Python API wrapper objects.
    """

    def __init__(self, url=None, username=None, password=None):
        self.url = urljoin(
            url or ENV["ATL_HOST_" + self.type.upper()], "/rest/api/latest/"
        )
        username = username or ENV["ATL_USER"]
        password = password or ENV["ATL_PASS"]
        self.auth = (  # Note: not used
            requests.auth.HTTPBasicAuth(username, password)
            if username and password
            else None
        )
        self.kwargs = {}
        if password.startswith("token:"):
            self.kwargs.setdefault("headers", {})
            self.kwargs["headers"]["Authorization"] = (
                "Bearer " + password[len("token:") :]
            )

    def get(self, api_path, **kwargs):
        response = requests.get(urljoin(self.url, api_path), **(self.kwargs | kwargs))
        response.raise_for_status()
        return response.json()

    def post(self, api_path, **kwargs):
        response = requests.post(urljoin(self.url, api_path), **(self.kwargs | kwargs))
        response.raise_for_status()
        return response.json()


class BitbucketAPI(APIWrapper):
    """Bitbucket API wrapper"""

    type = "Bitbucket"


class ConfluenceAPI(APIWrapper):
    """Confluence API wrapper"""

    type = "Confluence"


class JiraAPI(APIWrapper):
    """Jira API wrapper"""

    type = "Jira"


@cache
def epic_info():
    """Info. about epics, which are implemented as custom fields."""
    # these claim to require admin. which is not true
    # pprint(jira.get_custom_fields(search="Epic Link"))
    # pprint(jira.get_custom_fields(search="Epic Name"))
    jira_api = JiraAPI()
    fields = jira_api.get("field")
    epic_link = next(i for i in fields if i["name"] == "Epic Link")["id"]
    epic_name = next(i for i in fields if i["name"] == "Epic Name")["id"]
    types = jira_api.get("issuetype")
    epic_type = next(i for i in types if i["name"] == "Epic")["id"]
    return EpicInfo(link=epic_link, name=epic_name, type=epic_type)


def fetch(stub):
    """Generator of responses from limit / start methods.
    Let's you use
        search = atl_util.partial(jira.jql, f"project = {project}")
        print(len(list(atl_util.fetch(search))))
    to get all results iterated in blocks, but turns out
    jira.jql_get_list_of_tickets() does the same thing.
    """
    block_size = 50
    start = 0
    key = "issues"
    while (results := stub(limit=block_size, start=start))[key]:
        for result in results[key]:
            yield result
        start += block_size


def jql_result(jira, default, use_default=False):
    """Interactive JQL result with persistent history, client facing."""
    history = [
        readline.get_history_item(i)
        for i in range(1, readline.get_current_history_length() + 1)
    ]
    if default not in history:
        readline.add_history(default)
    try:
        return jql_result_interaction(jira, default=default if use_default else None)
    finally:
        readline.write_history_file(HISTORY)


def jql_result_interaction(jira, default=None):
    """Interactive JQL result with persistent history."""
    ok = False
    while not ok:
        if default:  # for dev., don't ask questions
            ok = True
            jql = default
        else:
            jql = input("JQL: ")
        results = jira.jql_get_list_of_tickets(jql)
        sys.stderr.write(f"{len(results)} results\n")
        for issue in results[:10]:
            sys.stderr.write(
                "%s %s %s\n"
                % (
                    issue["key"],
                    issue["fields"]["status"]["name"],
                    issue["fields"]["summary"],
                )
            )
        ok = default or "y" in input("Ok [y/N]: ").lower()
    return results


def jira_url(ticket: dict) -> str:
    """URL for Jira ticket."""
    return f"{ENV['ATL_HOST_JIRA']}/browse/{ticket['key']}"


def jira_link(ticket: dict, target="_issue") -> str:
    """Link for Jira ticket."""
    text = ticket["key"]
    if ticket["fields"]["status"]["name"] in STATUS_DONE:
        text = f"<s>{text}</s>"
    title = [
        f"{ticket['fields']['issuetype']['name']}: {ticket['fields']['summary']}"
        f" - {ticket['fields']['status']['name']}",
        " ".join(ticket["fields"]["labels"]),
        " ".join(i["name"] for i in ticket["fields"]["fixVersions"]),
    ]
    title = html.escape("\n".join(i.strip() for i in title if i.strip()))
    return f"<a target='{target}' href='{jira_url(ticket)}' title='{title}'>{text}</a>"


def graph_add(graph: dict, from_: dict, to: dict | None = None) -> None:
    """Add a link between to tickets in a graph."""
    graph.setdefault("edge", []).append((from_, to))


def fix_version(text):
    """Get version text, longest digits and dots"""
    texts = re.split("[^0-9.]+", text)
    texts.sort(key=len)
    return texts[-1]


def graph_to_dot(graph: dict, show_labels: Iterable[str] | None = None) -> str:
    """Generate graphviz dot source from graph."""
    show_labels = show_labels or []
    timestamp = f"Generated {time.asctime()}"
    dot = [f'digraph "{timestamp}" {{']
    attributes = defaultdict(str)
    for ticket in chain.from_iterable(graph["edge"]):
        if ticket is None:
            continue  # node passed without edges
        ticket["__key"] = ticket["key"].replace("-", "_")
        label = [ticket["key"]]
        if ticket["fields"]["issuetype"]["name"] == "Epic":
            label.append("\\n" + ticket["fields"][epic_info().name])
        if show_labels:
            label.append(
                "\\n"
                + " ".join(
                    i for i in show_labels if i in ticket["fields"].get("labels", [])
                )
            )
        for version in ticket["fields"].get("fixVersions", []):
            label[-1] += " " + fix_version(version["name"])

        label = "".join(label)
        attribs = {
            "fillcolor": NODE_COLOR.get(
                ticket["fields"]["status"]["name"], NODE_COLOR_DEFAULT
            ),
            "href": jira_url(ticket),
            "label": label,
            # Set shape by status or type
            "shape": NODE_SHAPE.get(
                ticket["fields"]["status"]["name"],
                NODE_SHAPE.get(
                    ticket["fields"]["issuetype"]["name"], NODE_SHAPE_DEFAULT
                ),
            ),
            "style": "filled",
            "tooltip": ticket["fields"]["summary"].replace('"', "'")
            + f" [{ticket['fields']['status']['name']}]",
            "target": "_ticket",
        }
        attribs = ";".join(f'{key}="{value}"' for key, value in attribs.items())
        if len(attribs) > len(attributes[ticket["__key"]]):
            # Process all tickets as some may be sparse vs. full data.
            # Keep the longest attribute sets generated.
            attributes[ticket["__key"]] = attribs
    for key, attribs in attributes.items():
        dot.append(f"{key} [{attribs}]")

    for from_, to in graph["edge"]:
        if to is None:
            continue
        attribs = {
            "color": EDGE_COLOR["Epic"]
            if from_["fields"]["issuetype"]["name"] == "Epic"
            else EDGE_COLOR_DEFAULT
        }
        attribs = ";".join(f'{key}="{value}"' for key, value in attribs.items())
        dot.append(f"{from_['__key']} -> {to['__key']} [{attribs}]")
    dot.append("}")
    return "\n".join(dot)


def recurse_pages(confl, page_id, state=None):
    """Yield descendant pages of Confluence page_id recursively."""
    if state is None:
        state = {"id_path": [], "title_path": []}
    for child in confl.get_child_pages(page_id):
        page = confl.get_page_by_id(child["id"])
        child_state = {
            "id_path": state["id_path"] + [child["id"]],
            "title_path": state["title_path"] + [page["title"]],
        }
        yield child_state
        yield from recurse_pages(confl, child["id"], state=child_state)
