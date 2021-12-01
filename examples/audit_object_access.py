import os
import json
import requests.exceptions

from thoughtspot import ThoughtSpot, MetadataNames

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

users_groups_id_name_map = {}

# Get users
users = ts.user.list()
print("Users")
print(users)
for user in users:
    users_groups_id_name_map[user['id']] = user['name']
# Get groups
groups = ts.group.list()
print("Groups")
print(groups)
for group in groups:
    users_groups_id_name_map[group['id']] = group['name']
# Permissions on liveboards

# Permissions call requires GUIDs, so must get list of all of them first
liveboards = ts.pinboard.list()
print("Liveboards")
print(liveboards)
lb_list = []
lb_id_name_map = {}
for lb in liveboards:
    lb_list.append(lb['id'])
    lb_id_name_map[lb['id']] = lb['name']
lb_perms = ts.tsrest.security_metadata_permissions(object_type=MetadataNames.PINBOARD, object_guids=lb_list,
                                                   dependent_share=True, permission_type='DEFINED')
print()
print(json.dumps(lb_perms, indent=1))
for perm in lb_perms:
    print(perm, lb_id_name_map[perm])
    perms_obj = lb_perms[perm]["permissions"]
    for p in perms_obj:
        print(p, users_groups_id_name_map[p])
    print("")

# Permissions for Answers
answers = ts.answer.list()
print("Answers")
print(answers)
a_list = []
a_id_name_map = {}
for a in answers:
    a_list.append(a['id'])
    a_id_name_map[a['id']] = a['name']
a_perms = ts.tsrest.security_metadata_permissions(object_type=MetadataNames.ANSWER, object_guids=a_list,
                                                   dependent_share=False, permission_type='DEFINED')

print()
print(json.dumps(a_perms, indent=1))
for perm in a_perms:
    print(perm, a_id_name_map[perm])
    perms_obj = a_perms[perm]["permissions"]
    for p in perms_obj:
        print(p, users_groups_id_name_map[p])
    print("")