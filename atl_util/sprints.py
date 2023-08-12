"""Analyze sprints."""
from collections import defaultdict
from pathlib import Path
from pprint import pformat, pprint

import atl_util
from ratelimit import limits, sleep_and_retry

ENV = atl_util.ENV
jira = atl_util.jira()

query = f"project = {atl_util.ENV['ATL_PROJECT']} status = Working"
todo = atl_util.jql_result(jira, query)

freq = defaultdict(int)
fullfreq = defaultdict(list)


@sleep_and_retry
@limits(calls=49, period=60)
def get_full(key):
    return jira.issue(key, expand="changelog")


for issue in todo:
    key = issue["key"]
    count = 0
    print(key, issue["fields"]["summary"])
    full = get_full(key)
    for history in full["changelog"]["histories"]:
        for item in history["items"]:
            if item["field"] == "Sprint":
                print(history["created"], "->", item["toString"])
                if item["toString"]:
                    count += 1
    freq[count] += 1
    fullfreq[count].append(key)
pprint(dict(freq))
Path("sprints.txt").write_text(pformat(dict(fullfreq)))
