"""Analyze epic release mapping."""
import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

query = (
    f"project = {atl_util.ENV['ATL_PROJECT']} "
    "and type = Epic and updated > startOfYear()"
)
print(query)
todo = jira.jql_get_list_of_tickets(query)

for epic in todo:
    issues = atl_util.partial(jira.epic_issues, epic["key"])
    issues = atl_util.fetch(issues)
    issues = list(issues)
    if issues:
        # print(sorted(list(issues[0]["fields"].keys())))
        releases = set([j["name"] for i in issues for j in i["fields"]["fixVersions"]])
        if "CCD 2.2.0 Release" in releases:
            print(epic["key"], epic["fields"]["summary"])
            print(releases)
            for issue in issues:
                if (
                    len(issue["fields"]["fixVersions"]) != 1
                    or issue["fields"]["fixVersions"][0]["name"] != "CCD 2.2.0 Release"
                ):
                    print(issue["key"], issue["fields"]["status"]["name"])
