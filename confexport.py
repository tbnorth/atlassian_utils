"""Experimental PanDoc export to GitHub Flavored Markdown."""
from io import StringIO
from pathlib import Path
from subprocess import run

import inquirer
from lxml import etree

import atl_util

ENV = atl_util.ENV


def soup(text):
    """Load XML soup from page content, determine type, epic."""
    if not text.strip():
        return {"type": "N/A", "epic": None}

    # nspace = "http://example.com/"
    # text = f"""<html xmlns:ac="{nspace}">{text}</html>"""
    text = text.replace("ac:", "")
    dom = etree.parse(StringIO(text), parser=etree.HTMLParser())
    # print(etree.dump(dom.getroot(), pretty_print=True))
    # print(dom.xpath("//parameter[@ac:name='key']"), namespaces={"ac": nspace})
    if dom.xpath("//structured-macro[@name='details']"):
        type_ = "requirements"
    else:
        type_ = "heading"
    epic = dom.xpath(
        "//structured-macro[@name='details']//parameter[@name='key']/text()"
    )
    assert len(epic) < 2
    epic = epic[0] if epic else None
    return {"type": type_, "epic": epic}


confluence = atl_util.confluence()
jira = atl_util.jira()

results = confluence.cql(f'''title = "{ENV['ATL_TARGET_TITLE']}"''')
page_id = results["results"][0]["content"]["id"]
space = confluence.get_page_space(page_id)
# pprint(list(confluence.get_child_pages(page_id)))
print(page_id)

epic_keys = []
for page in atl_util.recurse_pages(page_id):
    page = confluence.get_page_by_id(page["id"], expand="body.storage")
    try:
        storage = page["body"]["storage"]["value"]
    except KeyError:
        continue
    info = soup(storage)
    print(f"{page['title']} {info['type']} {info['epic']}")
    name = page["title"].replace(" ", "_").replace("/", "_")
    Path("out/" + name + ".html").write_text(storage)
    run(
        "pandoc -t gfm "
        # "-t markdown-simple_tables "
        # "-t markdown_github+pipe_tables-grid_tables "
        f"out/{name}.html -o out/{name}.md",
        shell=True,
    )
    run(
        "pandoc --standalone --embed-resources --metadata pagetitle=title "
        f"out/{name}.md -o out/{name}.2.html",
        shell=True,
    )

    continue
    if info["epic"]:
        epic_keys.append(info["epic"])
    if info["epic"]:
        # pprint(jira.issue(info["epic"]))
        print("-" * 80)
    if info["type"] == "requirements" and not info["epic"]:
        epic = jira.jql(f'''type = Epic and summary ~ "{page['title']}"''')
        # pprint(epic)
        if not epic.get("issues"):
            short = inquirer.prompt(
                [inquirer.Text("name", f"Name for epic '{page['title']}'")]
            )["name"]
            jira.issue_create(
                {
                    "project": {"key": ENV["ATL_PROJECT"]},
                    "summary": page["title"],
                    atl_util.epic_info().name: short,
                    # "issuetype": {"id": epic_type},
                    "issuetype": {"name": "Epic"},
                }
            )
        else:
            print(
                f"Epic exists but not set {page['title']} "
                f"{epic['issues'][0]['key']}."
            )

print(epic_keys)

# pprint(confluence.get_page_by_id(page_id, expand="body.storage"))
