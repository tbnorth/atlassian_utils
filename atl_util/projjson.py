"""Generate JSON data for a project plan.

Separated from markdown generation (projmd.py) to allow for GitHub Issues
based version.
"""
import json
import re
import time

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

REMOVE_CODE = re.compile(r"{code.*code}|\(\[ticket.*]\)", re.DOTALL)

print(f"Report generated {time.asctime()} from JIRA tickets")


query = ENV.get("ATL_JQL", "")
epics = atl_util.jql_result(jira, query)
jsons = []
response = {
    "generated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    "issues": jsons,
}
for epic in epics:
    jsons.append(
        {
            "summary": epic["fields"]["summary"],
            "full_description": epic["fields"]["description"],
            "description": REMOVE_CODE.sub("", epic["fields"]["description"] or ""),
            "priority": epic["fields"]["priority"]["id"],
            "key": epic["key"],
            "yamls": atl_util.yamls(epic),
        }
    )
print(json.dumps(response, indent=2))
open("proj.json", "w").write(json.dumps(response, indent=2))
