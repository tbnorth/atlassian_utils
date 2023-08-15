"""Create Confluence pages from a template for requirements."""
from html import unescape
from pprint import pprint  # noqa

import openpyxl
import requests
from ratelimit import limits, sleep_and_retry

import atl_util

ENV = atl_util.ENV
EI = atl_util.epic_info()
FY = ENV["ATL_CONF_REQ_FY"]

# A Jira link macro
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

# The line in the top table that needs to be replaced
ETARGET = "<th>Epic</th><td><br /></td>"

# Easier to use field names
XWALK = {
    "cat": "Category",
    "lead": "Lead",
    "type": "update type",
    "epic": "Epic",
    # "page": "anticipate including in CCD for FY24?",
    "page": "Confuence Page",
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
# Fields that shouldn't be listed as key: value pairs
USED = "cat", "epic", "page", "title", "desc"
# Checkmark columns for expected data availability
WHENS = "by Oct 1", "by Jan 1", "by April 1", "by July 1"
# Place in the template to insert our info.
TARGET = "<h2>4.0 High Level Requirements</h2>"


@sleep_and_retry
@limits(calls=49, period=60)
def slowly(func, *args, **kwargs):
    """Rate limit calls to Jira, Confluence."""
    return func(*args, **kwargs)


def get_or_create_epic(
    epic: str,  # Name of the epic, e.g. AOP24
    datas: list,  # List of dicts with data for each page
) -> str:
    """Get or create an epic."""
    existing_epic = slowly(jira.jql_get_list_of_tickets, f'"Epic Name" = {epic}')
    if existing_epic:
        return existing_epic[0]["key"]
    # Collect text to describe topic(s) covered by this epic
    desc = []
    pages = [i for i in datas if i["epic"] == epic]
    for page_i, page in enumerate(pages):
        if len(pages) > 1:
            desc.append(f"Topic {page_i + 1}")
        desc += [str(page["desc"])]
        # Add other fields as key: value pairs
        for key, value in page.items():
            if key not in USED and value is not None:
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
            "labels": [FY],
        },
    )["key"]

    return epic_key


def create_page(cat, epic, epic_key, pages):
    print("Skipped creation of pages", epic_key)
    return
    desc = [TARGET]  # inserting below this
    for page_i, page in enumerate(pages):
        if len(pages) > 1:
            desc.append(f"<p>Topic {page_i + 1}</p>")
        desc += [f"<p>{page['desc']}</p>"]
        for key, value in page.items():
            if key not in USED and value is not None:
                desc += [f"<div>{key}: {value}</div>"]
    desc = "\n".join(desc)
    template_inst = template["body"]["storage"]["value"]
    template_inst = template_inst.replace(TARGET, desc)
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


confluence = atl_util.confluence()
jira = atl_util.jira()
# Page to use as a template
template = slowly(confluence.get_page_by_id, ENV["ATL_CONF_TEMPLATE_ID"])
# Page to use as a parent to category pages
top = slowly(confluence.get_page_by_id, ENV["ATL_CONF_REQ_TOP"])

# Read data from Excel
wkbk = openpyxl.load_workbook("reqs.xlsx")
ws = wkbk.active
# Column names in row 2
col = [i.value for i in ws[2] if i.value]
# Column numbers by name
col = dict((k, v) for v, k in enumerate(col))
pages = 0
datas = []
for row in ws.iter_rows(min_row=3):
    data = dict((k, row[col[v]].value) for k, v in XWALK.items())
    cat = row[col["Category"]].value
    if "/" in cat:  # workaround for "Category 1 / Category 2" item
        cat = "All"
    data |= {
        "cat": cat,
        "data_when": next(
            (i for i in WHENS if "x" in (row[col[i]].value or "").lower()), None
        ),
    }
    if not data["epic"] or "n" in data["page"].lower():
        continue
    datas.append(data)

# Get set of Category, Epic pairs
epics = sorted(set((i["cat"], i["epic"]) for i in datas))
# Get parent pages for each category
parent = {}
for page in confluence.cql(f"parent={ENV['ATL_CONF_REQ_TOP']}")["results"]:
    if not page["title"].endswith(FY):
        continue
    parent[unescape(page["title"].rsplit(None, 1)[0])] = page["content"]["id"]
pprint(parent)
space = slowly(confluence.get_page_space, ENV["ATL_CONF_REQ_TOP"])
template = slowly(
    confluence.get_page_by_id, ENV["ATL_CONF_TEMPLATE_ID"], expand="body.storage"
)

item = 0  # Items covered (some pages cover multiple items)

# Create pages within each category
for epic_i, (cat, epic) in enumerate(epics, 1):
    epic_key = get_or_create_epic(epic, datas)
    print(f"{epic_i:2d}", cat, epic, epic_key)
    pages = [i for i in datas if i["epic"] == epic and i["cat"] == cat]
    title = pages[0]["title"]
    print(title)
    # Can't have same title in same space more than once
    if title.strip() in ("SeqAPASS", "invitroDB"):
        title = title.strip() + " II"
    results = slowly(confluence.cql, f"""title = '{title}' and parent={parent[cat]}""")
    results = results["results"]
    if not results:
        create_page(cat, epic, epic_key, pages)
    # Just feedback to show progress
    for page in pages:
        item += 1
        print(f"   {item:2d} {page['title']}")
