"""Utilities for accessing Atlassian services."""

import os
from collections import namedtuple
from functools import partial
from urllib.parse import urljoin
from pprint import pprint

import atlassian
import requests
from dotenv import load_dotenv

assert partial  # imported for client convenience

EpicInfo = namedtuple("EpicInfo", "name link type")

load_dotenv("atlassian.env")
ENV = os.environ


def __make_connection(type_):
    """Function factory for Bitbucket / Confluence / Jira connection functions.
    Uses the Python API wrapper objects.
    """

    def func(url=None, username=None, password=None):
        """Return required connection type."""
        return getattr(atlassian, type_)(
            url=url or ENV["ATL_HOST_" + type_.upper()],
            username=username or ENV["ATL_USER"],
            password=password or ENV["ATL_PASS"],
        )

    func.__doc__ = f"Return a {type_} connection."
    return func


bitbucket = __make_connection("Bitbucket")
confluence = __make_connection("Confluence")
jira = __make_connection("Jira")


class APIWrapper:
    """Wrapper for directs (requests) access to API for things not covered by the
    Python API wrapper objects.
    """

    def __init__(self, url=None, username=None, password=None):
        self.url = urljoin(
            url or ENV["ATL_HOST_" + self.type.upper()], "/rest/api/latest/"
        )
        username = username or ENV["ATL_USER"]
        password = password or ENV["ATL_PASS"]
        self.auth = (
            requests.auth.HTTPBasicAuth(username, password)
            if username and password
            else None
        )

    def get(self, api_path, **kwargs):
        response = requests.get(urljoin(self.url, api_path), **kwargs)
        response.raise_for_status()
        return response.json()

    def post(self, api_path, **kwargs):
        response = requests.post(urljoin(self.url, api_path), **kwargs)
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
