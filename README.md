# Utils. for Jira workflows

## Setup

    pip install -r requirements.txt
    cp atlassian.env.template atlassian.env
    # edit atlassian.env

To run tests, also `pip install pytest`.  Tests depend on content of and access to
Atlasian Jira, Confluence and Bitbucket.

Some scripts request JQL from the user, command line history is stored so up-arrow
can be used to re-use previous queries.

## Scripts

- **atl_util.py** - Core "library" for connections etc.
- **confread.py** - Read Confluence pages to check requirements / epics etc.
- **epicfix.py** - Add link to tickets to epic descriptions.
- **epicrelease.py** - Epic / release relationship.
- **epicstatus.py** - Analyze ticketing status of epics.
- **repomng.py** - List BB repos.
- **settags.py** - Set tags on tickets.
- **tagmunge.py** - Analyze duplicate tags.
- **triplet.py** - Create triplet of Data / API / UI tickets.
- uat_report.py - Generate UAT report.

- confexport.py - Export Confluence content to GitHub markdown.
- userlist.py - List users, API omits last login info.

## Notes

To make a password / token available without putting it atlantis.env, use

    read -s ATL_PASS
    export ATL_PASS

To run tests, use

    PYTHONPATH=. pytest tests -vv
