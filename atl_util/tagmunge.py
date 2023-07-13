"""Clean up labels"""
import json
from collections import defaultdict
from pathlib import Path
from pprint import pprint

import atl_util

assert pprint

jira = atl_util.jira()


def labels_in_project(project):
    """Seems only the Jira *Cloud* API supports retrieving a list of labels"""
    pass


project = "CE"
usage = defaultdict(int)
for ticket in jira.jql_get_list_of_tickets(f"project = {project}"):
    print(ticket["fields"]["labels"])
    for label in ticket["fields"]["labels"]:
        usage[label] += 1

usage = dict(sorted(usage.items(), key=lambda x: x[0].lower()))
json.dump(usage, Path(f"{project}-usage.json").open("w"), indent=4)
