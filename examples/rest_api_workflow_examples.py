import os
import requests.exceptions

from thoughtspot import ThoughtSpot

# The purpose of this is to show basic API workflows and how they are accomplished using the TSRestV1 class

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

# User Listing
print("\nUsers Listing")
users = ts.user.list_users()
print(users)

print("\nUsers Listing with Filter")
user = ts.user.list_users(filter="bryant.howell")
print(user)
user_id = user[0]["id"]

# Group Listing
print("\nGroups Listing")
groups = ts.group.list_groups()
print(groups)
print("\nGroups Listing with Filter")
group = ts.group.list_groups(filter='Administrator')
print(group)
group_id = group[0]['id']

# Users in a Group
print("\nUsers in Group - ID {}".format(group_id))
users_in_group = ts.group.list_users_in_group(group_guid=group_id)
print(users_in_group)
for u in users_in_group:

    print(u.keys())
    print(u['header']['id'], u['header']['name'], u['header']['displayName'])

# What can a User or Group see (Sharing)
objs_for_group = ts.group.list_available_objects_for_group(group_guid=group_id)
print(objs_for_group)
for obj in objs_for_group["headers"]:
    print(obj)

objs_for_user = ts.user.list_available_objects_for_user(user_guid=user_id)
print(objs_for_user)
for obj in objs_for_user["headers"]:
    print(obj)

# What Groups does a User Belong to (and other details)?
print("\nPrivileges for User {}".format(user_id))
user_privileges = ts.user.privileges_for_user(user_guid=user_id)
print(user_privileges)

print("\nAssigned Groups for User {}".format(user_id))
user_assigned_groups = ts.user.assigned_groups_for_user(user_guid=user_id)
print(user_assigned_groups)

print("\nInherited Groups for User {}".format(user_id))
user_inherited_groups = ts.user.inherited_groups_for_user(user_guid=user_id)
print(user_inherited_groups)

# Privileges for Group
print("\nPrivileges for Group {}".format(group_id))
group_privileges = ts.group.privileges_for_group(group_guid=group_id)
print(group_privileges)

# Usages of the user/sync capabilities
# User Update

# User Creation


# Group Creation