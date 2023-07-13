"""User info.

API doesn't report useful info. like last login.
"""

from pprint import pprint

import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()
start = 0
users = []
while True:
    block = jira.user_find_by_user_string(
        ".", start=start, limit=100, include_inactive_users=True
    )
    users += block
    if len(block) < 100:
        break
    start += 100
print(len(users))
pprint(users[0])
pprint(jira.user(users[0]['key']))
