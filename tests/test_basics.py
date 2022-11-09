import pytest
import requests

import atl_util


def test_bitbucket_api():
    bitbucket_api = atl_util.BitbucketAPI()
    assert len(bitbucket_api.get("projects")["values"]) > 10


def test_confluence_api():
    confluence_api = atl_util.ConfluenceAPI()
    assert len(confluence_api.get("space")["results"]) > 10


def test_jira_api():
    jira_api = atl_util.JiraAPI()
    assert len(jira_api.get("field")) > 10


def test_bitbucket():
    bitbucket = atl_util.bitbucket()
    thing = bitbucket.project_list()
    for i in range(10):
        next(thing)


def test_confluence():
    confluence = atl_util.confluence()
    thing = confluence.get_all_spaces()
    assert len(thing["results"]) > 10


def test_jira():
    jira = atl_util.jira()
    thing = jira.projects()
    assert len(thing) > 10


def test_jira_no_label_list():
    """List all labels API only in cloud version."""
    with pytest.raises(requests.exceptions.HTTPError):
        jira_api = atl_util.JiraAPI()
        assert len(jira_api.get("label")) > 10
