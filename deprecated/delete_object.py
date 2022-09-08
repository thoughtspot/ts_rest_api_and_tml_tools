import os
import requests.exceptions

from thoughtspot import ThoughtSpot, TSTypes

# This script uses the internal metadata/delete API endpoint, which will be unnecessary once the V2 API introduces
# a public form of delete. But it may be of use now

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

# Example of deleting a Liveboard with a known GUID
lb_guid = ''
# metadata/delete requires the object_type and a List of GUIDs to delete
ts.tsrest.metadata_delete(object_type=TSTypes.LIVEBOARD, guids=[lb_guid])

# You can chain this with the metadata/list calls to remove a whole set of items
lbs_with_a_tag = ts.tsrest.metadata_list(object_type=TSTypes.LIVEBOARD, tagname=['Old Stuff'])
guids_to_delete = []
for lb in lbs_with_a_tag['headers']:
    guids_to_delete.append(lb['id'])

ts.tsrest.metadata_delete(object_type=TSTypes.LIVEBOARD, guids=guids_to_delete)

# Alternatively, removing all sharing and switching ownership to a "dead content account" with
# ts.tsrest.user_transfer_ownership() is a safer move before deleting any content
