"""Analysis of data tickets"""
import csv
import datetime
import json
from pathlib import Path

import pytz
from dateutil.parser import parse

import atl_util

DATA = {}

jira = atl_util.jira()


def get_event(ticket, type, values, last=False):
    times = []
    for event in DATA["history"][ticket["key"]]["histories"]:
        for item in event["items"]:
            if item["field"] == type and item["toString"] in values:
                times.append((parse(event["created"]), item["toString"]))
    times.sort(reverse=last)
    if not times:
        return None
    return times[0][0]


def get_sprint(ticket):
    times = []
    for event in DATA["history"][ticket["key"]]["histories"]:
        for item in event["items"]:
            if item["field"] == "Sprint":
                times.append((parse(event["created"]), item["toString"]))
    times.sort()
    if not times:
        return None
    sprint = next((i for i in times[0][1].split() if i.startswith("20")), None)
    if sprint:
        date = parse(sprint)
        date = date.replace(
            tzinfo=pytz.timezone("America/New_York")
        ) - datetime.timedelta(days=14)
    return times[0][0]


def proc():
    out = open("data.csv", "w")
    writer = csv.writer(out)
    DATA["tickets"] = DATA.get("tickets") or atl_util.jql_result(jira, "")
    tickets = {i["key"]: i for i in DATA["tickets"]}
    DATA.setdefault("history", {})
    for key in tickets:
        if key in DATA["history"]:
            continue
        DATA["history"][key] = jira.get_issue_changelog(key)
    writer.writerow(
        [
            "issue",
            "blocked",
            "in_sprint",
            "resolved",
            "days",
            "in_progress",
            "in_done",
            "days",
        ]
    )
    for ticket in DATA["tickets"]:
        key = ticket["key"]
        # print(key)
        # date_start = parse(ticket["fields"]["created"])
        date_end = (
            parse(ticket["fields"]["resolutiondate"])
            if ticket["fields"]["resolutiondate"]
            else None
        )
        sprint = get_sprint(ticket)
        blocked = None
        for link in ticket["fields"]["issuelinks"]:
            if link["type"]["name"] == "Blocks":
                if "inwardIssue" in link:
                    # print(" <-", link["inwardIssue"]["key"])
                    pass
                if "outwardIssue" in link:
                    # print("  ->", link["outwardIssue"]["key"])
                    blocked = link["outwardIssue"]["key"]
                    break
        in_progress = get_event(ticket, "status", ["In Progress"])
        in_done = get_event(ticket, "status", ["In Review"], last=True) or get_event(
            ticket, "status", ["Done", "Abandon"], last=True
        )
        notime = lambda x: x.date().strftime("%Y-%m-%d") if x else None
        row = [
            atl_util.jira_url(ticket),
            blocked,
            # notime(date_start)
            notime(sprint),
            notime(date_end),
            (date_end - sprint).days if date_end and sprint else None,
            notime(in_progress),
            notime(in_done),
            (in_done - in_progress).days if in_done and in_progress else None,
        ]
        writer.writerow(row)


if __name__ == "__main__":
    if Path("data.json").exists():
        DATA |= json.load(open("data.json"))
    try:
        proc()
    finally:
        json.dump(DATA, open("data.json", "w"), indent=4)
