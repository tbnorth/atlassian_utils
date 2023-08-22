"""Create Confluence pages from a template for requirements."""
from html import unescape
from pprint import pprint  # noqa

from ratelimit import limits, sleep_and_retry

import atl_util

ENV = atl_util.ENV
EI = atl_util.epic_info()
FY = ENV["ATL_CONF_REQ_FY"]


@sleep_and_retry
@limits(calls=49, period=60)
def slowly(func, *args, **kwargs):
    """Rate limit calls to Jira, Confluence."""
    return func(*args, **kwargs)


confluence = atl_util.confluence()
jira = atl_util.jira()

# Get parent pages for each category
parent = {}
for page in slowly(confluence.cql, f"parent={ENV['ATL_CONF_REQ_TOP']}")["results"]:
    if not page["title"].endswith(FY):
        continue
    parent[unescape(page["title"].rsplit(None, 1)[0])] = page["content"]["id"]
pprint(parent)
space = slowly(confluence.get_page_space, ENV["ATL_CONF_REQ_TOP"])
item = 0  # Items covered (some pages cover multiple items)
api = atl_util.ConfluenceAPI()
for title, parent_id in parent.items():
    for page in slowly(confluence.cql, f"parent={parent_id}")["results"]:
        title = unescape(page["title"])
        page_id = page["content"]["id"]
        print(f"Page: {title}")
        slowly(
            api.post,
            f"content/{page_id}/label",
            json=[{"prefix": "global", "name": "requirements"}],
        )
