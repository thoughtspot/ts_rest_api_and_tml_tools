import os
import requests.exceptions
import json
import csv

from thoughtspot import ThoughtSpot, MetadataNames
from tml import *

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


table_tml_start = Table.generate_tml_from_scratch(connection_name=connection_name, db_name=db_name, schema=schema,
                                                  db_table=db_table)

yaml_ordereddict = YAMLTML.load_string_to_ordereddict(table_tml_start)
table_obj = Table(tml_dict=yaml_ordereddict)

print(YAMLTML.dump_tml_object_to_yaml_string(table_obj))

#
# Create the columns from the REST API calls
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



# If you do not have the GUID, use to find by name
#connections = ts.tsrest.metadata_listobjectheaders(object_type=MetadataNames.CONNECTION, filter='Connection Name')

# metadata/details provides the connection_config needed for the connection/create and connection/update commands
connection_details = ts.tsrest.metadata_details(object_type=MetadataNames.CONNECTION, object_guids=[connection_guid])

# These helper functions parse out the parts you need from very complex connection_details object
connection_config = ts.tsrest.get_connection_config_from_metadata_details(connection_details)
connection_name = ts.tsrest.get_connection_name_from_metadata_details(connection_details)
connection_type = ts.tsrest.get_connection_type_from_metadata_details(connection_details)

columns = ts.tsrest.connection_fetch_live_columns(connection_guid=connection_guid,
                                                  config_json_string=json.dumps(connection_config),
                                                  database_name=db_name, schema_name=schema, table_name=db_table)

tml_columns_dict_list = create_tml_table_columns_from_rest_api_response(rest_api_columns=columns)
table_obj.add_columns(tml_columns_dict_list)

print(YAMLTML.dump_tml_object_to_yaml_string(table_obj))

#
# Create columns from an input file (CSV)
#


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


tml_columns_dict_list = create_tml_table_columns_input_file('column_input.csv')
table_obj.add_columns(tml_columns_dict_list)

print(YAMLTML.dump_tml_object_to_yaml_string(table_obj))

#
# Example of creating worksheet from a table
#

# get a valid table from ThoughtSpot as TML
table_guid = '760603dc-8ae9-4557-8c39-e5dd6cc09453'
table_resp = ts.tsrest.metadata_tml_export(guid=table_guid)
table_tml_obj = Table(table_resp)


new_worksheet_name = 'Worksheet Test 1'

ws_start = Worksheet.generate_tml_from_scratch(worksheet_name=new_worksheet_name, table_name=table_tml_obj.content_name)
ws_obj = Worksheet(YAMLTML.load_string_to_ordereddict(ws_start))
print(ws_start)

new_ws_cols = create_worksheet_columns_from_table_object(table_obj=table_tml_obj)
ws_obj.add_worksheet_columns(new_ws_cols)

print(YAMLTML.dump_tml_object_to_yaml_string(ws_obj))
fh = open('test.worksheet.tml', mode='w')
fh.write(YAMLTML.dump_tml_object_to_yaml_string(ws_obj))
fh.close()

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
# Import the new worksheet (publish) to ThoughtSpot
#
import_response = ts.tsrest.metadata_tml_import(tml=ws_obj.tml, create_new_on_server=True)

new_guids = ts.tsrest.guids_from_imported_tml(import_response)
new_ws_guid = new_guids[0]

# From here, you can take existing template Answers and Liveboards and switch their existing Worksheet reference to
# match the new_ws_guid value
# See tml_change_references_example.py on how to perform this swap and publish new

