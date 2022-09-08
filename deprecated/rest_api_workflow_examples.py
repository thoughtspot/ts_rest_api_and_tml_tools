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
users = ts.user.list()
print(users)

print("\nUsers Listing with Filter")
user = ts.user.list(filter="bryant.howell")
print(user)
user_id = user[0]["id"]

# Group Listing
print("\nGroups Listing")
groups = ts.group.list()
print(groups)
print("\nGroups Listing with Filter")
group = ts.group.list(filter='Administrator')
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

print("\n Available Objects for Users")
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

print("\nIs User {} a Super User".format(user_id))
user_inherited_groups = ts.user.is_user_superuser(user_guid=user_id)
print(user_inherited_groups)

print("\nState of User {} ".format(user_id))
user_inherited_groups = ts.user.state_of_user(user_guid=user_id)
print(user_inherited_groups)

# Privileges for Group
print("\nPrivileges for Group {}".format(group_id))
group_privileges = ts.group.privileges_for_group(group_guid=group_id)
print(group_privileges)

# Usages of the user/sync capabilities
# User Update

# User Creation
ts.tsrest.user__post()

# Group Creation

# Share content with a group

group_guid = ts.group.find_guid('Group Name')

perms = ts.answer.create_share_permissions(read_only_users_or_groups_guids=[group_guid])

answer_guid = '6336a2e5-dbe0-4118-b167-6f1e07fbac84'
ts.answer.share([answer_guid], perms)