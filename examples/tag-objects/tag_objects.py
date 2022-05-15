import os

import requests.exceptions

from thoughtspot import MetadataNames, ThoughtSpot

# This script uses the internal metadata/delete API endpoint, which will be unnecessary once the V2 API introduces
# a public form of delete. But it may be of use now

username = os.getenv("username")  # or type in yourself
password = os.getenv("password")  # or type in yourself
server = os.getenv("server")  # or type in yourself

ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)


lb_guids = ["{guid_1}", "{guid_2}"]

# Get tag GUIDs from a list of names
tags_response = ts.tsrest.metadata_listobjectheaders(object_type=MetadataNames.TAG)
tag_names_to_get_guid = ["Tag 1", "Tag 2"]
tag_guids = []

for t in tags_response:
    if t["name"] in tag_names_to_get_guid:
        tag_guids.append(t["id"])


# The wrapper functions have an "assign_tags"
ts.liveboard.assign_tags(object_guids=lb_guids, tag_guids=tag_guids)

# Which are equivalent to using metadata/assigntag with the specific object_type
ts.tsrest.metadata_assigntag(object_guids=lb_guids, object_type=MetadataNames.LIVEBOARD, tag_guids=tag_guids)
