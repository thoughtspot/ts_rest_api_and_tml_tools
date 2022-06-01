import os
import requests.exceptions
from thoughtspot import ThoughtSpot, MetadataNames

#
# This script is an example of a workflow useful in a Git-based SDLC process
# It transfers the ownership of objects in ThoughtSpot to a Service Account
# Transfer Ownership command requires knowing the existing owner, so this takes
# the GUID inputs, finds the owners, and constructs the minimum number of ownership transfer commands
#

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

# Service account username
transfer_to_username = 'service.account'


# Process to get the GUIDs of the objects to transfer may vary
# This is basically pseudo-code
# Metadata requests require knowing the object type, so it makes sense to split the response
def get_guids_by_object_type():
    # However you determine which objects, packaged them up by types
    guid_return = { MetadataNames.LIVEBOARD : [] ,
                    MetadataNames.ANSWER : [] ,
                    MetadataNames.WORKSHEET: []
                    }
    return guid_return


# Given the guids, determine the owner username, which is necessary in the object transfer command
def get_guid_ownership(guids):
    # Object headers request only returns GUID of owner, but transfer ownership requires username
    # You could request all users, then do lookup. But number of users may be large relative to who
    # is modifying content
    users = ts.tsrest.user_list()
    # Make a quick lookup dict of the user info based on GUID
    users_map = {}
    for u in users:
        users_map[u['id']] = u

    # Will be { 'owner_username1' : [ 'guid1', guid2'], 'owner_username2': ['guid3', 'guid4']
    owner_username_object_guid_map = {}
    # Assuming the dict format from get_guids(), with object_type as first key then list of guids
    for object_type in guids:
        # Getting object headers
        obj_headers = ts.tsrest.metadata_listobjectheaders(object_type=object_type, fetchids=guids[object_type])

        # Grab all the owner GUIDs to find
        for o in obj_headers:
            owner_username = users_map[o['owner']]
            # Create an array for the owner user to store objects if doesn't exist
            if owner_username not in owner_username_object_guid_map:
                owner_username_object_guid_map[owner_username] = []
            # add the GUID to the list for that owner
            owner_username_object_guid_map[owner_username].append(o['id'])

    return owner_username_object_guid_map


object_guids_by_type = get_guids_by_object_type()
owner_username_to_guid_map = get_guid_ownership(object_guids_by_type)
for owner in owner_username_to_guid_map:
    # It is possible you need to batch the GUIDs given enough objects being transferred
    # because the GUIDs are added into the URL rather than sent in POST data
    # Something like:  if len(owner_username_to_guid_map[owner]) > 20:
    ts.tsrest.user_transfer_ownership(current_owner_username=owner, new_owner_username=transfer_to_username,
                                      object_guids=owner_username_to_guid_map[owner])