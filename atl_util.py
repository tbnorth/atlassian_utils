"""Utilities for accessing Atlassian services."""

import os
from collections import namedtuple

import atlassian
import requests
from dotenv import load_dotenv

EpicInfo = namedtuple("EpicInfo", "name link type")

load_dotenv("atlassian.env")
ENV = os.environ


def __make_connection(type_):
    """Function factory for Bitbucket / Confluence / Jira connection functions."""
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


def epic_info():
    """Info. about epics, which are implemented as custom fields."""
    # these claim to require admin. which is not true
    # pprint(jira.get_custom_fields(search="Epic Link"))
    # pprint(jira.get_custom_fields(search="Epic Name"))
    fields = requests.get(ENV["ATL_HOST_JIRA"] + "/rest/api/latest/field").json()
    epic_link = next(i for i in fields if i["name"] == "Epic Link")["id"]
    epic_name = next(i for i in fields if i["name"] == "Epic Name")["id"]
    types = requests.get(ENV["ATL_HOST_JIRA"] + "/rest/api/latest/issuetype").json()
    epic_type = next(i for i in types if i["name"] == "Epic")["id"]
    return EpicInfo(link=epic_link, name=epic_name, type=epic_type)
