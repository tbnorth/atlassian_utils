"""Recursively publish markdown files to Confluence."""
import json
import subprocess
import sys
from pathlib import Path

import atl_util


def pandoc_markdown_first_header(text: str) -> str:
    """Get first header from pandoc markdown."""
    text = subprocess.run(
        "pandoc -t json", input=text, capture_output=True, shell=True
    ).stdout
    data = json.loads(text)
    for block in data["blocks"]:
        if block["t"] == "Header":
            header = [i["c"] for i in block["c"][2] if i["t"] == "Str"]
            return " ".join(header)


def recurse_md_files(path, state=None):
    """Yield descendant pages of Confluence page_id recursively."""
    if state is None:
        state = {"path": Path(path), "title_path": []}
    for child in path.glob("*"):
        if child.is_file():
            title = pandoc_markdown_first_header(child.read_bytes())
            child_state = {
                "path": child,
                "title": title,
            }
            yield child_state
        elif child.is_dir():
            child_state = {
                "path": child,
            }
            yield from recurse_md_files(child, state=child_state)


ENV = atl_util.ENV
confluence = atl_util.confluence()
results = confluence.cql(f'''title = "{ENV['ATL_TARGET_TITLE']}"''')
page_id = results["results"][0]["content"]["id"]
space = confluence.get_page_space(page_id)
# pprint(list(confluence.get_child_pages(page_id)))
print(page_id)
# new_page = confluence.create_page(space, "Test", "Test", parent_id=page_id)
top = Path(sys.argv[1])
for state in recurse_md_files(top):
    print(state)
for state in atl_util.recurse_pages(confluence, page_id):
    print(state)
