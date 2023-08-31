"""Create Confluence pages from a template for requirements."""
from html import unescape
# from pathlib import Path
from io import StringIO
from pprint import pprint  # noqa

import atl_util
from ratelimit import limits, sleep_and_retry

ENV = atl_util.ENV
EI = atl_util.epic_info()
FY = ENV["ATL_CONF_REQ_FY"]

from lxml import etree

COUNT = """
<ac:structured-macro ac:name="jira"
ac:schema-version="1"
ac:macro-id="aa257632-ddb3-4019-b988-a0e77e37b62b">
  <ac:parameter ac:name="server">EPA JIRA</ac:parameter>
  <ac:parameter ac:name="jqlQuery">"Epic Link" = {key}</ac:parameter>
  <ac:parameter ac:name="count">true</ac:parameter>
  <ac:parameter ac:name="serverId">29e39f89-57e1-3d0a-93ec-d11e0fd160ca</ac:parameter>
</ac:structured-macro>"""

// WARNING - not reliably detecting existing count macro

@sleep_and_retry
@limits(calls=90, period=60)
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
        content = slowly(confluence.get_page_by_id, page_id, expand="body.storage")
        # if "/" not in title:
        #     Path(f"{title}.html").write_text(content["body"]["storage"]["value"])
        text = content["body"]["storage"]["value"]
        text = text.replace("ac:", "ac_")
        dom = etree.parse(StringIO(text), parser=etree.HTMLParser())
        td = dom.xpath(
            "//td[.//ac_structured-macro[@ac_macro-id="
            "'1247a0fb-274f-437c-b68a-57eb8816b048']]"
        )
        assert len(td) < 2
        if not td:
            print(f"Skipping {title}")
            continue
        epic = td[0].xpath(
            ".//ac_structured-macro[@ac_macro-id='1247a0fb-274f-437c-b68a-57eb8816b048'"
            "]/ac_parameter[@ac_name='key']/text()"
        )[0]
        print(f"Epic: {epic}")
        if td[0].xpath(
            ".//ac_structured-macro[@ac_macro-id="
            "'aa257632-ddb3-4019-b988-a0e77e37b62b']"
        ):
            print(f"Count present: {title}")
            continue
        text = content["body"]["storage"]["value"]
        pos = text.index("1247a0fb-274f-437c-b68a-57eb8816b048")
        pos2 = text.index("</p></div>", pos)
        print(f"Insert at {pos2-pos}")
        text = text[:pos2] + COUNT.format(key=epic) + text[pos2:]
        # slowly(
        #     confluence.update_page,
        #     title=title,
        #     page_id=page_id,
        #     body=text,
        # )
