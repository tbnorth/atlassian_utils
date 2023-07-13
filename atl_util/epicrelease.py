"""Analyze epic release mapping."""
import atl_util

ENV = atl_util.ENV
jira = atl_util.jira()

query = (
    f"project = {atl_util.ENV['ATL_PROJECT']} "
    "and type = Epic and updated > startOfYear()"
)
print(query)
todo = atl_util.jql_result(jira, query)

for epic in todo:
    issues = atl_util.partial(jira.epic_issues, epic["key"])
    issues = list(atl_util.fetch(issues))
    if issues:
        # print(sorted(list(issues[0]["fields"].keys())))
        releases = set([j["name"] for i in issues for j in i["fields"]["fixVersions"]])
        if ENV["ATL_TARGET_RELEASE"] in releases:
            print("\nEPIC:", epic["key"], epic["fields"]["summary"])
            # print(releases)
            for issue in issues:
                if (
                    len(issue["fields"]["fixVersions"]) != 1
                    or issue["fields"]["fixVersions"][0]["name"] != "CCD 2.2.0 Release"
                ):
                    print("ISSUE:", issue["key"], issue["fields"]["status"]["name"])
