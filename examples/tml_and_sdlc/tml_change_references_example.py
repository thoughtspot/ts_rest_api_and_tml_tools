import os
import requests
from thoughtspot import *
from thoughtspot_tml import *

#
# Simple examples of swapping references on the various object types
# More complete workflows in other example files
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
# Repoint Answer to different Worksheet (or single table)
#

# The simplest operation is to change an Answer connected to a single Worksheet or Table
# Always use a Worksheet when you have a more complicated data model

answer_guid = ''
# Create the Answer object from TML Exported via REST API
answer_obj = Answer(ts.tml.export_tml(guid=answer_guid))

# Alternatively, open from disk and load using YAMLTML
# fh = open('filename.tml', 'r')
# yaml_str = fh.read()
# fh.close()
# answer_obj = Answer(YAMLTML.load_string_to_ordereddict(yaml_str))

new_worksheet_guid = ''  # Get this from REST API metadata_listobjectheaders call or result of previous process
original_worksheet_name = answer_obj.tables[0]['name']  # Use to find the original name
answer_obj.change_worksheets_by_fqn(name_to_guid_map={original_worksheet_name: new_worksheet_guid})

# If you are going to import to create new, can remove the GUID for safety
# answer_obj.remove_guid()

# Export to disk

with open('{}-modified.answer.tml'.format(answer_guid), 'w', encoding='utf-8') as fh:
    fh.write(YAMLTML.dump_tml_object(answer_obj))

# Import directly to ThoughtSpot
try:
    import_response = ts.tml.import_tml(tml=answer_obj.tml, create_new_on_server=True)
    new_guids = ts.tsrest.guids_from_imported_tml(import_response)
    new_answer_guid = new_guids[0]
# Some TML errors come back in the JSON response of a 200 HTTP, but a SyntaxError will be thrown
except SyntaxError as e:
    print('TML import encountered error:')
    print(e)
    exit()  # Or do something else


#
# Repoint Visualizations on Liveboard to different Worksheet
#

# Liveboards have a number of Visualization objects which have the same structure as an Answer
# But each Visualization could be pointed to different Worksheets
# This is why the name_to_guid_map exists

orig_ws_name_to_new_guid_map = { 'worksheet 1': 'newGuid1', 'Worksheet 2': 'newGuid2'}

lb_guid = ''
lb_obj = Liveboard(ts.tml.export_tml(guid=lb_guid))
lb_obj.remap_worksheets_to_new_fqn(name_to_guid_map=orig_ws_name_to_new_guid_map)

# If you are going to import to create new, can remove the GUID for safety
# lb_obj.remove_guid()

# Export to disk

with open('{}-modified.liveboard.tml'.format(lb_guid), 'w', encoding='utf-8') as fh:
    fh.write(YAMLTML.dump_tml_object(answer_obj))

# Import directly to ThoughtSpot
import_response = ts.tml.import_tml(tml=lb_obj.tml, create_new_on_server=True)
new_guids = ts.tsrest.guids_from_imported_tml(import_response)
new_lb_guid = new_guids[0]

#
# Repoint Worksheet to new tables
#

ws_guid = ""
ws_obj = Worksheet(ts.tml.export_tml(guid=ws_guid))
# Building out this mapping is the biggest challenge. Easiest if you know the set of tables vs. trying to find in all
orig_table_name_to_new_guid_map = { 'table name 1': 'newGuid1', 'table name 2': 'newGuid2'}
ws_obj.remap_tables_to_new_fqn(name_to_fqn_map=orig_table_name_to_new_guid_map)

# If you are going to import to create new, can remove the GUID for safety
# ws_obj.remove_guid()

# Export to disk

with open('{}-modified.worksheet.tml'.format(ws_guid), 'w', encoding='utf-8') as fh:
    fh.write(YAMLTML.dump_tml_object(ws_obj))

# Import directly to ThoughtSpot
try:
    import_response = ts.tml.import_tml(tml=ws_obj.tml, create_new_on_server=True)
    new_guids = ts.tsrest.guids_from_imported_tml(import_response)
    new_ws_guid = new_guids[0]
# Some TML errors come back in the JSON response of a 200 HTTP, but a SyntaxError will be thrown
except SyntaxError as e:
    print('TML import encountered error:')
    print(e)
    exit()  # Or do something else



#
# Switch Table Connection details
#

# Table reference Connections directly and include details about the table on the databasse itself
# As long as the table you switch to has the same schema (column names and types), switching these details will work
# You can also modify columns or try and build from scratch (see tml_from_scratch.py example)

table_guid = ""
table_obj = Table(ts.tml.export_tml(guid=table_guid))
# Connection names are unique and don't require a GUID ever
table_obj.connection_name = 'New Connection Name'
table_obj.db_name = 'NEW_DB_NAME'
table_obj.schema = 'DIFFERENT_SCHEMA'
table_obj.db_table = 'DIFFERENT_TABLE'

# If you are going to import to create new, can remove the GUID for safety
# table_obj.remove_guid()

# Export to disk

with open('{}-modified.table.tml'.format(ws_guid), 'w', encoding='utf-8') as fh:
    fh.write(YAMLTML.dump_tml_object(ws_obj))

# Import directly to ThoughtSpot
try:
    import_response = ts.tml.import_tml(tml=table_obj.tml, create_new_on_server=True)
    new_guids = ts.tsrest.guids_from_imported_tml(import_response)
    new_table_guid = new_guids[0]

# Some TML errors come back in the JSON response of a 200 HTTP, but a SyntaxError will be thrown
except SyntaxError as e:
    print('TML import encountered error:')
    print(e)
    exit()  # Or somethign else

