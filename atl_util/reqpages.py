"""Create Confluence pages from a template for requirements."""
from html import unescape
from pprint import pprint  # noqa

import openpyxl
import requests
from ratelimit import limits, sleep_and_retry

import atl_util

ENV = atl_util.ENV
EI = atl_util.epic_info()

EPIC = (
    '<div class="content-wrapper"><p><ac:structured-macro '
    'ac:name="jira" ac:schema-version="1" '
    'ac:macro-id="1247a0fb-274f-437c-b68a-57eb8816b048"><ac:parameter '
    'ac:name="server">EPA '
    "JIRA</ac:parameter><ac:parameter "
    'ac:name="columnIds">issuekey,summary,issuetype,created,updated,duedate,assignee,'
    "reporter,priority,status,resolution</ac:parameter><ac:parameter "
    'ac:name="columns">key,summary,type,created,updated,due,assignee,reporter,priority,'
    'status,resolution</ac:parameter><ac:parameter ac:name="serverId">'
    "29e39f89-57e1-3d0a-93ec-d11e0fd160ca</ac:parameter><ac:parameter "
    'ac:name="key">{issue_key}</ac:parameter></ac:structured-macro></p></div>'
)

ETARGET = "<th>Epic</th><td><br /></td>"


@sleep_and_retry
@limits(calls=49, period=60)
def slowly(func, *args, **kwargs):
    return func(*args, **kwargs)


def get_or_create_epic(epic, datas):
    alt_epic = slowly(jira.jql_get_list_of_tickets, f'"Epic Name" = {epic}')
    epic_key = alt_epic[0]["key"] if alt_epic else None
    if epic_key:
        return epic_key
    desc = []
    pages = [i for i in datas if i["epic"] == epic]
    for page_i, page in enumerate(pages):
        if len(pages) > 1:
            desc.append(f"Topic {page_i + 1}")
        desc += [str(page["desc"])]
        for key, value in page.items():
            if key not in used and value is not None:
                desc += [f"\n\n{key}: {value}"]
    desc = "\n\n".join(desc)
    epic_key = slowly(
        jira.issue_create,
        {
            "project": {"key": ENV["ATL_PROJECT"]},
            "summary": page["title"],
            "issuetype": {"name": "Epic"},
            EI.name: epic,
            "description": desc,
            "labels": ["FY24"],
        },
    )["key"]

    slowly(jira.update_issue_field, epic_key, {"labels": ["FY24"]})
    return epic_key


confluence = atl_util.confluence()
jira = atl_util.jira()
template = slowly(confluence.get_page_by_id, ENV["ATL_CONF_TEMPLATE_ID"])
top = slowly(confluence.get_page_by_id, ENV["ATL_CONF_REQ_TOP"])

wkbk = openpyxl.load_workbook("reqs.xlsx")
ws = wkbk.active
col = [i.value for i in ws[2] if i.value]
col = dict((k, v) for v, k in enumerate(col))
whens = "by Oct 1", "by Jan 1", "by April 1", "by July 1"
pages = 0
datas = []
xwalk = {
    # "cat": "Category",  # see below
    "lead": "Lead",
    "type": "update type",
    "epic": "Epic",
    "page": "anticipate including in CCD for FY24?",
    "title": "Items",
    "desc": "Dependencies/comments",
    "source": "Data source",
    "rapid_numb": "RAPID number",
    "links": "RAPID/Jira URL",
    "rapid": "RAPID anticipated compl date",
    "data_avail": "final data avail now?",
    "data_cleared": "Are data cleared?",
    "done": "Nisha's thoughts on FYQ",
}
used = "cat", "epic", "page", "title", "desc"
ywalk = dict((v, k) for k, v in xwalk.items())
for row in ws.iter_rows(min_row=3):
    cat = row[col["Category"]].value
    if "/" in cat:
        cat = "All"
    data = {
        "cat": cat,
        "data_when": next(
            (i for i in whens if "x" in (row[col[i]].value or "").lower()), None
        ),
    }
    data |= dict((k, row[col[v]].value) for k, v in xwalk.items())
    if not data["epic"] or "n" in data["page"].lower():
        continue
    datas.append(data)
epics = sorted(set((i["cat"], i["epic"]) for i in datas))
parent = {}
# for page in slowly(atl_util.recurse_pages, confluence, ENV["ATL_CONF_REQ_TOP"]):
for page in confluence.cql(f"parent={ENV['ATL_CONF_REQ_TOP']}")["results"]:
    if not page["title"].endswith("FY24"):
        continue
    parent[unescape(page["title"].rsplit(None, 1)[0])] = page["content"]["id"]
pprint(parent)
item = 0
space = slowly(confluence.get_page_space, ENV["ATL_CONF_REQ_TOP"])
template = slowly(
    confluence.get_page_by_id, ENV["ATL_CONF_TEMPLATE_ID"], expand="body.storage"
)
target = "<h2>4.0 High Level Requirements</h2>"
for epic_i, (cat, epic) in enumerate(epics, 1):
    epic_key = get_or_create_epic(epic, datas)
    print(f"{epic_i:2d}", cat, epic, epic_key)
    pages = [i for i in datas if i["epic"] == epic and i["cat"] == cat]
    title = pages[0]["title"]
    print(title)
    if title.strip() in ("SeqAPASS", "invitroDB"):
        title = title.strip() + " II"
    print(title)
    results = slowly(confluence.cql, f"""title = '{title}' and parent={parent[cat]}""")
    results = results["results"]
    assert len(results) < 2, f"Too many results for {title}"
    desc = [target]
    if not results:
        for page_i, page in enumerate(pages):
            if len(pages) > 1:
                desc.append(f"<p>Topic {page_i + 1}</p>")
            desc += [f"<p>{page['desc']}</p>"]
            for key, value in page.items():
                if key not in used and value is not None:
                    desc += [f"<div>{key}: {value}</div>"]
        desc = "\n".join(desc)
        template_inst = template["body"]["storage"]["value"]
        template_inst = template_inst.replace(target, desc)
        assert ETARGET in template_inst, f"Can't find {ETARGET}"
        new = ETARGET.replace("<br />", EPIC.format(issue_key=epic_key))
        template_inst = template_inst.replace(ETARGET, new)
        try:
            slowly(
                confluence.create_page,
                space,
                title,
                template_inst,
                parent_id=parent[cat],
            )
        except requests.exceptions.HTTPError:
            print("   Already exists or other failure")
    for page in pages:
        item += 1
        print(f"   {item:2d} {page['title']}")
