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


def create_id_name_dict(listobjectheaders_response):
    mapping_dict = {}
    for a in listobjectheaders_response:
        mapping_dict[a["id"]] = a["name"]
    return mapping_dict


def get_permissions_for_all_objects(object_type, listobjectheaders_response, permission_type='DEFINED', dependent_share=True):
    id_map = create_id_name_dict(listobjectheaders_response)
    perms = ts.tsrest.security_metadata_permissions(object_type=object_type, object_guids=list(id_map.keys()),
                                                    dependent_share=dependent_share, permission_type=permission_type)
    return perms


def map_names_to_permissions(listobjectheaders_response, permissions, users_map, groups_map):
    obj_id_map = create_id_name_dict(listobjectheaders_response)

    final_perms = permissions.copy()

    for perm in final_perms:
        # print(obj_id_map[perm], ":", perm)
        # Add name property
        perms_obj = final_perms[perm]["permissions"]
        final_perms[perm]["name"] = obj_id_map[perm]
        for p in perms_obj:
            # GUIDs can be for USER or USER_GROUP, this figures out which and marks along with adding the name
            if p in users_map:
                # print("  User: ", users_map[p], p)
                # Add User name and type
                final_perms[perm]["permissions"][p]["name"] = users_map[p]
                final_perms[perm]["permissions"][p]["type"] = "USER"
            if p in groups_map:
                # print("  Group: ", groups_map[p], p)
                # Add Group name and type
                final_perms[perm]["permissions"][p]["name"] = groups_map[p]
                final_perms[perm]["permissions"][p]["type"] = "USER_GROUP"
        # print("")


    return final_perms


# Get users
users = ts.user.list()
print("Users")
print(users)
user_id_name_map = create_id_name_dict(users)

# Get groups
groups = ts.group.list()
group_id_name_map = create_id_name_dict(groups)
# Permissions on liveboards

# Permissions call requires GUIDs, so must get list of all of them first
liveboards = ts.pinboard.list()

answers = ts.answer.list()
a_perms = get_permissions_for_all_objects(object_type=MetadataNames.ANSWER, listobjectheaders_response=answers)
a_perms_with_names = map_names_to_permissions(listobjectheaders_response=answers, permissions=a_perms, users_map=user_id_name_map,
                         groups_map=group_id_name_map)

print(json.dumps(a_perms_with_names, indent=2))