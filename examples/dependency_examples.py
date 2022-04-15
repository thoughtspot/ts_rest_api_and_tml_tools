import os
import requests.exceptions
import json
from collections import OrderedDict
from thoughtspot import ThoughtSpot, MetadataNames

#
# Example of using the dependency endpoints to find out about related objects
# Dependency API looks from parent to furthest child
# Child objects already have reference to their direct parent, but there is no "to the root parent" direct lookup
#
#
# Liveboards and Answers don't have dependencies at this time (even though there are endpoints to look at them)
# Instead you might want to know: what data sources do this Liveboard or Answer attach to?
#
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

#
# Dependencies from Table in connection
#


# Parses the dependency responses to return only the object types and a list of GUIDs,
# which can be input into other commands to take action
def get_dependent_objects_guid_map(dependent_objects_response):
    # You might have a reason to deal with object types in a particular order
    # For example, if you are deleting things, you would do Liveboards and Answers first, then Worksheets,
    # before the tables themselves
    obj_type_guid_map = OrderedDict(
        {
            MetadataNames.LIVEBOARD: [],
            MetadataNames.ANSWER: [],
            MetadataNames.WORKSHEEET: [],
            MetadataNames.TABLE: []
        }
    )
    dep_objs = dependent_objects_response
    # First level of response is the GUID of the requested object
    for obj in dep_objs:
        # For every object_type, there is a key for a List of the objects of that type
        for obj_type in dep_objs[obj]:
            #print(obj_type)
            # The objects of each type as object structures, with 'id' property and other metadata details
            for o in dep_objs[obj][obj_type]:
                #print(o)
                obj_type_guid_map[obj_type].append(o['id'])
    return obj_type_guid_map


def get_dependent_objects_for_table(table_guid: str):
    #print('Dependencies for Table')

    try:
        dep_objs = ts.table.get_dependent_objects(table_guids=[table_guid])
        print("Dependent objects response for table {} :".format(table_guid))
        print(dep_objs)

        dep_objs_guid_map = get_dependent_objects_guid_map(dep_objs)
        print("Dependent objects mapping by type for table {}".format((table_guid)))
        print(dep_objs_guid_map)

        for obj_type in dep_objs_guid_map:
            if len(dep_objs_guid_map[obj_type]) > 0:
                #
                #
                # HERE YOU WOULD PUT THE ACTION YOU WANT TO ACCOMPLISH WITH THE DEPENDENCIES
                #
                #
                pass  # comment out and add section for what you'd like to do, examples below

                # Example action of deleting all of the objects
                # print('Deleting {} objects: {}'.format(obj_type, dep_objs_guid_map[obj_type]))
                # ts.tsrest.metadata_delete(object_type=obj_type, guids=dep_objs_guid_map[obj_type])

                # Alternatively, you could TAG each object
                # tag_guids = [ts.tag.find_guid('Tag To Use')]
                # print('Tagging {} objects: {}'.format(obj_type, dep_objs_guid_map[obj_type]))
                # ts.tag.assign_tags(object_guids=dep_objs_guid_map[obj_type], tag_guids=tag_guids)

    except requests.exceptions.HTTPError as e:
        print(e.request.url)
        print(e.response.status_code)
        print(e.response.content)
        exit()


#
# Dependencies from Worksheet
#

# If you get from the table or connection level, the dependency API will give you any objects that descend from that Worksheet
def get_dependent_objects_for_worksheet(ws_guid: str):
    # print('\nDependencies for Worksheet')

    try:
        dep_objs = ts.worksheet.get_dependent_objects(worksheet_guids=[ws_guid])
        print("Dependent objects response for worksheet {} :".format(ws_guid))
        print(dep_objs)

        dep_objs_guid_map = get_dependent_objects_guid_map(dep_objs)
        print("Dependent objects mapping by type for worksheet {}".format((ws_guid)))
        print(dep_objs_guid_map)

        for obj_type in dep_objs_guid_map:
            if len(dep_objs_guid_map[obj_type]) > 0:
                #
                #
                # HERE YOU WOULD PUT THE ACTION YOU WANT TO ACCOMPLISH WITH THE DEPENDENCIES
                #
                #
                pass  # comment out and add section for what you'd like to do, examples below

                # Example action of deleting all of the objects
                # print('Deleting {} objects: {}'.format(obj_type, dep_objs_guid_map[obj_type]))
                # ts.tsrest.metadata_delete(object_type=obj_type, guids=dep_objs_guid_map[obj_type])

    except requests.exceptions.HTTPError as e:
        print(e.request.url)
        print(e.response.status_code)
        print(e.response.content)
        exit()


#
# main section showing functional patterns:
#


# Dependencies for a whole Connection
# Pulls the tables for the connection, then looks at dependencies for each one
def dependencies_from_a_connection(connection_guid=None, connection_name=None):
    # Connection names are unique, you can always do lookup
    if connection_guid is not None:
        conn_guid = ts.connection.find_guid(name=connection_name)
    else:
        conn_guid = connection_guid
    tables_in_connection = ts.connection.list_tables_for_connection(connection_guid=conn_guid)
    print(tables_in_connection)
    print("Looping through each table")
    for table_guid in tables_in_connection:
        print("Looking at table {}".format(table_guid))
        # Do whatever dependency lookups and actions in this loop
        get_dependent_objects_for_table(table_guid=table_guid)


# Tables can have the same name, so having other way to find GUID is important
# This function will do a simple lookup for table_name if you don't pass in table_guid (requires connection_guid),
# but you may want to do metadata_list or metadata_listobjheaders calls to filter or use tags etc. to find the GUID
def dependencies_from_a_table(table_guid=None, table_name=None, connection_guid=None):
    # Connection names are unique, you can always do lookup
    if table_guid is not None:
        # We use Connection GUID for precision, tables can often have the same name when coming from different connections
        t_guid = ts.table.find_guid(name=table_name, connection_guid=connection_guid)
    else:
        t_guid = table_guid

    # Define all the rest of your actions in this function
    get_dependent_objects_for_table(t_guid)


# Worksheets can have the same name, even with tables from same connection so having other way to find GUID is important
# This function will do a simple lookup for ws_name if you don't pass in ws_guid, but you may want to do other
# metadata_list or metadata_listobjheaders calls to filter or use tags etc. to find the GUID
def dependencies_from_a_worksheet(ws_guid=None, ws_name=None):
    # Connection names are unique, you can always do lookup
    if ws_guid is not None:
        # We use Connection GUID for precision, tables can often have the same name when coming from different connections
        w_guid = ts.worksheet.find_guid(name=ws_name)
    else:
        w_guid = ws_guid

    # Define all the rest of your actions in this function
    get_dependent_objects_for_worksheet(ws_guid=w_guid)



