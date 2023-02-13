# Utils. for Jira workflows

- **atl_util.py** - Core "library" for connections etc.
- **confread.py** - Read Confluence pages to check requirements / epics etc.
- **epicfix.py** - Add link to tickets to epic descriptions.
- **epicrelease.py** - Epic / release relationship.
- **epicstatus.py** - Analyze ticketing status of epics.
- **repomng.py** - List BB repos.
- **settags.py** - Set tags on tickets.
- **tagmunge.py** - Analyze duplicate tags.
- **triplet.py** - Create triplet of Data / API / UI tickets.

- confexport.py - Export Confluence content to GitHub markdown.
- userlist.py - List users, API omits last login info.

## Notes

    read -s ATL_PASS
    export ATL_PASS
    PYTHONPATH=. pytest tests -vv
