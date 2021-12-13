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
    # Because the GUIDs pass in the URL, there is a limit to how many can be requested at a time
    # Must batch through the full set, make whatever number of requests, then put the whole thing together
    batch_size = 20
    guids_list = list(id_map.keys())
    # Reverse the list so that pop can run from the end of the list, more efficient
    guids_list.reverse()
    # Pop out the first elements in the batch size
    guids_to_retrieve = []
    for i in range(batch_size):
        guids_to_retrieve.append(guids_list.pop())
    # Get the first permissions object, we'll add the elements from subsequent calls to it
    perms = ts.tsrest.security_metadata_permissions(object_type=object_type, object_guids=guids_to_retrieve,
                                                    dependent_share=dependent_share, permission_type=permission_type)
    # The pop() action is reducing the list size so that eventually it will be at 0
    while len(guids_list) > 0:
        guids_to_retrieve = []
        for i in range(batch_size):
            # pop() throws IndexError once List is empty
            try:
                guids_to_retrieve.append(guids_list.pop())
            # break the loop after the last item
            except IndexError:
                break
        # Request the next batch of permissions by GUID
        next_perms = ts.tsrest.security_metadata_permissions(object_type=object_type, object_guids=guids_to_retrieve,
                                                    dependent_share=dependent_share, permission_type=permission_type)
        for p in next_perms:
            perms[p] = next_perms[p]

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


def objects_without_permissions(permissions_object):
    final_obj = permissions_object.copy()
    for perm in permissions_object:
        if len(permissions_object[perm]["permissions"]) > 0:
            del final_obj[perm]
    return final_obj


def objects_with_permissions(permissions_object):
    final_obj = permissions_object.copy()
    for perm in permissions_object:
        if len(permissions_object[perm]["permissions"]) == 0:
            del final_obj[perm]
    return final_obj


# Get users
users = ts.user.list()
user_id_name_map = create_id_name_dict(users)

# Get groups
groups = ts.group.list()
group_id_name_map = create_id_name_dict(groups)
# Permissions on liveboards


answers = ts.answer.list()
a_perms = get_permissions_for_all_objects(object_type=MetadataNames.ANSWER, listobjectheaders_response=answers)
a_perms_with_names = map_names_to_permissions(listobjectheaders_response=answers, permissions=a_perms, users_map=user_id_name_map,
                        groups_map=group_id_name_map)

# Permissions call requires GUIDs, so must get list of all of them first
liveboards = ts.pinboard.list()

a_with_perms = objects_with_permissions(a_perms_with_names)
print(json.dumps(a_with_perms, indent=2))

a_without_perms = objects_without_permissions(a_perms_with_names)
print(json.dumps(a_without_perms, indent=2))

l_perms = get_permissions_for_all_objects(object_type=MetadataNames.PINBOARD, listobjectheaders_response=liveboards)
print(l_perms)
l_perms_with_names = map_names_to_permissions(listobjectheaders_response=liveboards, permissions=l_perms, users_map=user_id_name_map,
                       groups_map=group_id_name_map)


l_with_perms = objects_with_permissions(l_perms_with_names)
print(json.dumps(l_with_perms, indent=2))

