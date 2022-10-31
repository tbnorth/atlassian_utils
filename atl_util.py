"""Utilities for accessing Atlassian services."""

import os
from collections import namedtuple

import atlassian
import requests
from dotenv import load_dotenv

EpicInfo = namedtuple("EpicInfo", "name link type")

load_dotenv("atlassian.env")
ENV = os.environ


def confluence():
    """A Confluence connection."""
    return atlassian.Confluence(
        url=ENV["ATL_HOST_CONFLUENCE"],
        username=ENV["ATL_USER"],
        password=ENV["ATL_PASS"],
    )


def jira():
    """A Jira connection."""
    return atlassian.Jira(
        url=ENV["ATL_HOST_JIRA"], username=ENV["ATL_USER"], password=ENV["ATL_PASS"]
    )


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
