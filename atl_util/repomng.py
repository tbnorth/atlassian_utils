"""List BB repos. etc."""
from pprint import pprint

import atl_util

ENV = atl_util.ENV

bitbucket = atl_util.bitbucket()

# pprint(list(bitbucket.project_list()))

pprint(list(bitbucket.repo_list(f"~{ENV['ATL_USER']}")))
