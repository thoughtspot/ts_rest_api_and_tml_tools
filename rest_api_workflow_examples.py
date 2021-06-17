import os
import requests.exceptions

from tsrest import TSRestV1, MetadataNames, ShareModes

# The purpose of this is to show basic API workflows and how they are accomplished using the TSRestV1 class

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: TSRestV1 = TSRestV1(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

# User Listing
users = ts.get_users()
print(users)

user = ts.get_users(filter="bryant.howell")
print(user)
user_id = user[0]["id"]

# Group Listing
groups = ts.get_groups()
print(groups)
group = ts.get_groups(filter='Developers')
print(group)

# Users in a Group
group = ts.get_groups(filter='Developers')
group_id = None
for g in group:
    group_id = g["id"]
print(group_id)
users_in_group = ts.get_users_in_group(group_guid=group_id)
print(users_in_group)
for u in users_in_group:
    #print(u)
    print(u['header']['id'], u['header']['name'], u['header']['displayName'])

# What can a User or Group see (Sharing)
objs_for_group = ts.get_available_objects(user_or_group_guid=group_id, user_or_group=MetadataNames.GROUP)
print(objs_for_group)
for obj in objs_for_group["headers"]:
    print(obj)

objs_for_user = ts.get_available_objects(user_or_group_guid=user_id,user_or_group=MetadataNames.USER)
print(objs_for_user)
for obj in objs_for_user["headers"]:
    print(obj)

# What Groups does a User Belong to (and other details)?
user_details = ts.metadata_details(object_type=MetadataNames.USER, object_guids=[user_id])
print(user_details)
for a in user_details["storables"][0]:
    print(a, user_details["storables"][0][a])
    #print(user_details["storables"][0]['userContent'][a])

user_privileges = ts.get_user_privileges(user_guid=user_id)


# Usages of the user/sync capabilities
# User Update

# User Creation


# Group Creation