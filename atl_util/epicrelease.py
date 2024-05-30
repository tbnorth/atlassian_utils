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
    epic_releases = set(i["name"] for i in epic["fields"]["fixVersions"])
    epic_status = epic["fields"]["status"]["name"]
    issues = atl_util.partial(jira.epic_issues, epic["key"])
    issues = list(atl_util.fetch(issues))
    releases = set([j["name"] for i in issues for j in i["fields"]["fixVersions"]])
    if issues:
        # print(sorted(list(issues[0]["fields"].keys())))
        print(
            "\nEPIC:",
            epic["key"],
            epic["fields"]["summary"],
            epic_status,
            epic_releases,
        )
        if releases != epic_releases:
            print("ISSUE RELEASES:", releases)
        releases = set([j["name"] for i in issues for j in i["fields"]["fixVersions"]])
        ok = 0
        for issue in issues:
            errs = []
            if (
                len(issue["fields"]["fixVersions"]) != 1
                or issue["fields"]["fixVersions"][0]["name"] not in epic_releases
            ):
                errs.append("Release mismatch with epic")
                if (
                    epic_releases
                    and not issue["fields"]["fixVersions"]
                    # undo "Old"/"Future" if epic was initially send there then moved
                    or issue["fields"]["fixVersions"][0]["name"] == "Old"
                    or issue["fields"]["fixVersions"][0]["name"] == "Future"
                ):
                    jira.update_issue_field(
                        issue["key"],
                        {"fixVersions": [epic["fields"]["fixVersions"][0]]},
                    )
            if epic_status == "Done" and issue["fields"]["status"]["name"] not in (
                "Done",
                "Ice Box",
            ):
                errs.append("Status mismatch with epic")
            if (
                issue["fields"]["status"]["name"] == "Done"
                and issue["fields"]["fixVersions"]
                and issue["fields"]["fixVersions"][0]["name"] == "Future"
            ):
                errs.append("Future ticket already done")
            if errs:
                print(
                    "ISSUE:",
                    issue["key"],
                    issue["fields"]["status"]["name"],
                    issue["fields"]["fixVersions"][0]["name"]
                    if issue["fields"]["fixVersions"]
                    else "UNASSIGNED (fixed automatically if possible)",
                )
                print("\n".join(errs))
            else:
                ok += 1

        print(f"{ok} issues OK")
        # print(
        #     f'{ENV["ATL_HOST_JIRA"]}/issues/?jql="Epic Link"={epic["key"]} and '
        #     f'fixVersion != "{ENV["ATL_TARGET_RELEASE"]}"'
        # )
