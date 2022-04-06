import os
import requests.exceptions
import json

from thoughtspot import ThoughtSpot, MetadataNames

#
# Example of using the dependency endpoints to find out about related objects
# Dependency API looks from parent to furthest child
# Child objects already have reference to their direct parent, but there is no "to the root parent" direct lookup
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
# Dependencies for a whole Connection
#

# Connection will have any number of Table objects, which you can retrieve and then iterate through
connection_name = 'Bryant Snowflake'
c_guid = ts.connection.find_guid(name=connection_name)
tables_in_connection = ts.table.list_tables_for_connection(connection_guid=c_guid)
print(tables_in_connection)
for t in tables_in_connection:
    print(t)
    # Do whatever dependency lookups and actions in this loop

#
# Dependencies from Table in connection
#
print('Dependencies for Table')

table_name = 'V_DENORM_VITAMIN_SUPPLEMENTS'
# We use Connection GUID for precision, tables can often have the same name when coming from different connections
t_guid = ts.table.find_guid(name=table_name, connection_guid=c_guid)
try:
    dep_objs = ts.table.get_dependent_objects(table_guids=[t_guid])
    print(dep_objs)
except requests.exceptions.HTTPError as e:
    print(e.request.url)
    print(e.response.status_code)
    print(e.response.content)
    exit()

# First level of response is the GUID of the requested object
for obj in dep_objs:
    # For every object_type, there is a key for a List of the objects of that type
    for obj_type in dep_objs[obj]:
        print(obj_type)
        # The objects of each type as object structures, with 'id' property and other metadata details
        for o in dep_objs[obj][obj_type]:
            print(o)


#
# Dependencies from Worksheet
#
print('\nDependencies for Worksheet')

ws_name = 'Worksheet Test 2'
# Worksheets can have the same name, even with tables from same connection so having other way to find GUID is important
# ws_guid = ts.worksheet.find_guid(name=ws_name)
ws_guid = 'b7daaf5a-e7c7-4268-9bfa-3e21717cdfd1'
try:
    dep_objs = ts.worksheet.get_dependent_objects(worksheet_guids=[ws_guid])
    print(dep_objs)
except requests.exceptions.HTTPError as e:
    print(e.request.url)
    print(e.response.status_code)
    print(e.response.content)
    exit()

# First level of response is the GUID of the requested object
for obj in dep_objs:
    # For every object_type, there is a key for a List of the objects of that type
    for obj_type in dep_objs[obj]:
        print(obj_type)

        # The objects of each type as object structures, with 'id' property and other metadata details
        for o in dep_objs[obj][obj_type]:
            print(o)

#
# Liveboards and Answers don't have dependencies at this time (even though there are endpoints to look at them)
# Instead you might want to know: what data sources do this Liveboard or Answer attach to?
#