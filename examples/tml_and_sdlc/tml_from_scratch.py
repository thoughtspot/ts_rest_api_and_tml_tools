import os
import requests.exceptions
import json
import csv

from thoughtspot import ThoughtSpot, MetadataNames
from thoughtspot_tml import *

#
# This script shows how to create a valid Table TML from scratch, rather than modifying an existing TML from ThoughtSpot
# From a single table, you can also create a valid Worksheet.
# This facilitates adding data sources to ThoughtSpot that have been newly created within a data source
#

# Connection to get details from
connection_guid = ''
# You could do lookup instead to get the connection name (or do the other way around)
connection_name = 'Snowflake'

db_name = ""
schema = ''
db_table = ""

# Username to Share To
username_to_share = ''

# Group Name to Share To
group_name_to_share = ''

# The connection_fetch_live_columns() REST API returns a response with column information for a given table
# pulled through JDBC connection in ThoughtSpot. This function iterates through an creates a List of column dictionaries
# to be added to a Table object using Table.add_columns
def create_tml_table_columns_from_rest_api_response(rest_api_columns):
    new_columns = []
    for t in rest_api_columns:
        for c in rest_api_columns[t]:
            col_name = c['name']
            col_data_type = c['type']
            col_type = 'ATTRIBUTE'
            # Simple algorithm for making numeric columns MEASURE by default
            if col_data_type in ['DOUBLE', 'INT64']:
                col_type = 'MEASURE'
            new_column = table_obj.create_column(column_display_name=col_name,
                                                 db_column_name=col_name,
                                                 column_data_type=col_data_type, column_type=col_type)
            new_columns.append(new_column)
    return new_columns


# Worksheets have their own column references which refer to elements within the Table they connect to.
# This function takes a Table object and generates the worksheet columns as a list of dicts
# Which can be added using Worksheet.add_worksheet_columns()
def create_worksheet_columns_from_table_object(table_obj: Table, ws_table_path_id: str = None):
    if ws_table_path_id is None:
        # Default is just to add "_1" to the table name
        ws_table_path_id = table_obj.content_name + "_1"
    table_cols = table_obj.columns
    ws_cols = []
    for c in table_cols:
        #print(c)
        if 'index' in c['properties']:
            index_type = c['properties']['index']
        else:
            index_type = 'DEFAULT'
        new_ws_col = Worksheet.create_worksheet_column(column_display_name=c['name'], ws_table_path_id=ws_table_path_id,
                                                       table_column_name=c['name'],
                                                       column_type=c['properties']['column_type'],
                                                       index_type=index_type)
        ws_cols.append(new_ws_col)
    return ws_cols


#
# Sign in to ThoughtSpot REST API
#
username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

# ThoughtSpot class wraps the V1 REST API
ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)
#
# End of Sign In
#

#
# Create the initial Table Object
#


# Set the display name for the Table in ThoughtSpot
new_table_name = 'Nice Name for Table'
# Create the YAML string for the table with the desired properties
table_tml_start = Table.generate_tml_from_scratch(connection_name=connection_name,
                                                  db_name=db_name,
                                                  schema=schema,
                                                  db_table=db_table,
                                                  table_name=new_table_name)

# TML objects are created from an OrderedDict, so this converts from raw YAML string to that OrderedDict
yaml_ordereddict = YAMLTML.load_string(table_tml_start)
table_obj = Table(tml_dict=yaml_ordereddict)

#
# End of Create initial Table Object
#

#
# Create the columns from the REST API calls - comment out if using Create from CSV Input below
#


# If you do not have the Connection GUID, UNCOMMENT to lookup the GUID by name
# connections = ts.tsrest.metadata_listobjectheaders(object_type=MetadataNames.CONNECTION, filter=connection_name)
# connection_guid = connections[0]['id']

# metadata/details provides the connection_config needed for the connection/create and connection/update commands
connection_details = ts.tsrest.metadata_details(object_type=MetadataNames.CONNECTION, object_guids=[connection_guid])

# These helper functions parse out the parts you need from very complex connection_details object
connection_config = ts.tsrest.get_connection_config_from_metadata_details(connection_details)
connection_name = ts.tsrest.get_connection_name_from_metadata_details(connection_details)
connection_type = ts.tsrest.get_connection_type_from_metadata_details(connection_details)

# connection_fetch_live_columns retrieves all columns and types for a table via ThoughtSpot's JDBC connection
columns = ts.tsrest.connection_fetch_live_columns(connection_guid=connection_guid,
                                                  config_json_string=json.dumps(connection_config),
                                                  database_name=db_name, schema_name=schema, table_name=db_table)

# Function parses the columns REST API response from above into the format for the Table.add_columns() method
tml_columns_dict_list = create_tml_table_columns_from_rest_api_response(rest_api_columns=columns)
table_obj.add_columns(tml_columns_dict_list)

final_table_yaml_str = YAMLTML.dump_tml_object(table_obj)
print(final_table_yaml_str)
final_table_filename = 'table_output.table.tml'
with open(final_table_filename, 'w', encoding='utf-8') as fh:
    fh.write(final_table_yaml_str)

#
# End of Create the columns from the REST API calls
#

#
# Create columns from an input file (CSV) -- comment out if using Create from REST API
#

# This section defines a CSV format (which includes a header row) to create a table from

# 'CSV' format for a table is
# db_column_name|column_name|data_type|attribute_or_measure|index_type
def create_tml_table_columns_input_file(filename):
    new_columns = []
    with open(filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter='|', quotechar='"')

        row_count = 0
        for row in csvreader:
            # skip header
            if row_count == 0:
                row_count = 1
                continue
            db_col_name = row[0]
            col_name = row[1]
            col_data_type = row[2]
            col_type = row[3]
            index_type = row[4]
            # Simple algorithm for making numeric columns MEASURE by default
            if col_data_type in ['DOUBLE', 'INT64']:
                col_type = 'MEASURE'
            new_column = table_obj.create_column(column_display_name=col_name,
                                                 db_column_name=db_col_name,
                                                 column_data_type=col_data_type, column_type=col_type,
                                                 index_type=index_type)
            new_columns.append(new_column)
    return new_columns


table_csv_input_filename = 'column_input.csv'
tml_columns_dict_list = create_tml_table_columns_input_file(table_csv_input_filename)
table_obj.add_columns(tml_columns_dict_list)

print(YAMLTML.dump_tml_object(table_obj))
final_table_filename = 'table_output_from_csv.table.tml'
with open(final_table_filename, 'w', encoding='utf-8') as fh:
    fh.write(final_table_yaml_str)

#
# End of Create Columns from CSV Input
#

#
# Import the Table into ThoughtSpot
#

# Publish the new Table, check for TML validation issues
try:
    # You could run this with validate_only=True first to check any issues
    import_response = ts.tml.import_tml(tml=table_obj.tml, create_new_on_server=True, validate_only=False)

# Some TML errors come back in the JSON response of a 200 HTTP, but a SyntaxError will be thrown
except SyntaxError as e:
    print('TML import encountered error:')
    print(e)
    # Choose how you want to recover from here if there are issues (possibly not exit whole script)
    exit()

# Get the GUID from the newly created object
new_guids = ts.tsrest.guids_from_imported_tml(import_response)
new_table_guid = new_guids[0]

# Sharing the content
# Get the GUIDs for users or groups you want to share the content to
group_guid = ts.group.find_guid(group_name_to_share)
user_guid = ts.user.find_guid(username_to_share)

# Create the Share structure
perms = ts.table.create_share_permissions(read_only_users_or_groups_guids=[group_guid, user_guid])
# Share the object
ts.table.share([new_table_guid], perms)

#
# End Import Table into ThoughtSpot
#

#
# Create Worksheet from an existing Table object
#

# Display name of the new Worksheet in ThoughtSpot
new_worksheet_name = 'Worksheet Test 1'

# get a valid table from ThoughtSpot as TML
# Here we get the table object we publsihed earlier
table_resp = ts.tsrest.metadata_tml_export(guid=new_table_guid)
table_tml_obj = Table(table_resp)

# Exports the necessary YAML string to create a Worksheet object
ws_start = Worksheet.generate_tml_from_scratch(worksheet_name=new_worksheet_name, table_name=table_tml_obj.content_name)
# Build the Worksheet object from the initial YAML string
ws_obj = Worksheet(YAMLTML.load_string(ws_start))
print(ws_start)

# Automatically build the columns based on the columns in the table, then add to the Worksheet (starts with no columns)
new_ws_cols = create_worksheet_columns_from_table_object(table_obj=table_tml_obj)
ws_obj.add_worksheet_columns(new_ws_cols)

# Add the Table GUID reference to make sure it connects without issue
# We're not really remapping here, just swapping in the GUID instead of the name of the same Table object
ws_obj.remap_tables_to_new_fqn({new_table_name : new_table_guid})

# Output the Worksheet to disk to review
final_ws_yaml_string = YAMLTML.dump_tml_object(ws_obj)
# print(final_ws_yaml_string)
with open('test.worksheet.tml', mode='w', encoding='utf-8') as fh:
    fh.write(final_ws_yaml_string)

#
# End Create Worksheet from Existing Table Object
#

#
# Create Worksheet from an input file
#


# The identifiers use the 'name' property from a Table (not the 'db_table_name') and the table_path_id from
# within the Worksheet (which is an alias of the table itself)
# table_column_name|worksheet_column_name|attribute_or_measure|index_type
def create_worksheet_columns_input_file(filename, ws_table_path_id: str = None):
    if ws_table_path_id is None:
        # Default is just to add "_1" to the table name
        ws_table_path_id = table_obj.content_name + "_1"
    ws_cols = []
    with open(filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter='|', quotechar='"')
        row_count = 0
        for row in csvreader:
            # skip header
            if row_count == 0:
                row_count = 1
                continue

            table_column_name = row[0]
            col_name = row[1]
            column_type = row[2]
            index_type = row[3]

            new_ws_col = Worksheet.create_worksheet_column(column_display_name=col_name,
                                                           ws_table_path_id=ws_table_path_id,
                                                           table_column_name=table_column_name,
                                                           column_type=column_type,
                                                           index_type=index_type)
            ws_cols.append(new_ws_col)
    return ws_cols


#
# End Create Worksheet from Input File
#

#
# Import the Worksheet (publish) to ThoughtSpot
#

# Publish the new Worksheet, check for TML validation issues
try:
    # You could run this with validate_only=True first to check any issues
    import_response = ts.tml.import_tml(tml=ws_obj.tml, create_new_on_server=True, validate_only=False)

# Some TML errors come back in the JSON response of a 200 HTTP, but a SyntaxError will be thrown
except SyntaxError as e:
    print('TML import encountered error:')
    print(e)
    # Choose how you want to recover from here if there are issues (possibly not exit whole script)
    exit()

new_guids = ts.tsrest.guids_from_imported_tml(import_response)
new_ws_guid = new_guids[0]

# Create the Share structure
perms = ts.worksheet.create_share_permissions(read_only_users_or_groups_guids=[group_guid, user_guid])
# Share the object
ts.worksheet.share([new_ws_guid], perms)

#
# End Import the Worksheet
#

# From here, you can take existing template Answers and Liveboards and switch their existing Worksheet reference to
# match the new_ws_guid value
# See tml_change_references_example.py on how to perform this swap and publish new

#
# Answer Template from Disk, change reference to new Worksheet and Import
#

template_answer_file = 'template.answer.tml'
with open(template_answer_file, 'r') as fh:
    a_obj = Answer(YAMLTML.load_string(fh.read()))

# replace_worksheet() changes the reference within the Answer to a different existing Worksheet object in ThoughtSpot
# We're just changing things to the object loaded in memory in Python, never writing back to disk
a_obj.replace_worksheet(new_worksheet_name=new_worksheet_name, new_worksheet_guid_for_fqn=new_ws_guid)
a_obj.remove_guid()  # just in case

# Publish the modified Answer, check for TML validation issues
try:
    # You could run this with validate_only=True first to check any issues
    import_response = ts.tml.import_tml(tml=a_obj.tml, create_new_on_server=True, validate_only=False)

# Some TML errors come back in the JSON response of a 200 HTTP, but a SyntaxError will be thrown
except SyntaxError as e:
    print('TML import encountered error:')
    print(e)
    # Choose how you want to recover from here if there are issues (possibly not exit whole script)
    exit()

new_answer_guids = ts.tsrest.guids_from_imported_tml(import_response)
new_answer_guid = new_answer_guids[0]

# Create the Share structure
perms = ts.answer.create_share_permissions(read_only_users_or_groups_guids=[group_guid, user_guid])
# Share the object
ts.answer.share([new_answer_guid], perms)

#
# End Answer Template from Disk, change reference to new Worksheet and Import
#

#
# Liveboard Template from Disk, change reference to new Worksheet and Import
#

template_liveboard_file = 'template.liveboard.tml'
with open(template_liveboard_file, 'r') as fh:
    lb_obj = Liveboard(YAMLTML.load_string(fh.read()))

# Changes the reference to Worksheet in the template from template worksheet to
lb_obj.replace_worksheet_on_all_visualizations(new_worksheet_name=new_worksheet_name,
                                               new_worksheet_guid_for_fqn=new_ws_guid)
lb_obj.remove_guid()  # just in case

# Publish the new Liveboard, check for TML validation issues
try:
    # You could run this with validate_only=True first to check any issues
    import_response = ts.tml.import_tml(tml=lb_obj.tml, create_new_on_server=True, validate_only=False)
    # Some TML errors come back in the JSON response of a 200 HTTP, this function creates exception if errors
    response_details = ts.tsrest.raise_tml_errors(import_response)

# Some TML errors come back in the JSON response of a 200 HTTP, but a SyntaxError will be thrown
except SyntaxError as e:
    print('TML import encountered error:')
    print(e)
    # Choose how you want to recover from here if there are issues (possibly not exit whole script)
    exit()

new_lb_guids = ts.tsrest.guids_from_imported_tml(import_response)
new_lb_guid = new_lb_guids[0]

# Create the Share structure
perms = ts.liveboard.create_share_permissions(read_only_users_or_groups_guids=[group_guid, user_guid])
# Share the object
ts.liveboard.share([new_lb_guid], perms)

#
# End Liveboard Template from Disk, change reference to new Worksheet and Import
#
