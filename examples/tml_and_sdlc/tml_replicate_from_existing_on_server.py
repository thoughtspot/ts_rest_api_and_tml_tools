import os
import oyaml as yaml
import requests
from thoughtspot import *
from thoughtspot_tml import *

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
# NOTE ON JOINS (also noted in README):
# To ensure that TML publishing works,
# you should manually add some type of random number or alphanumeric to the end of the automatically generated JOIN name
# so that every JOIN has a unique name.
# Ex. If you have a JOIN named "DIM_TABLE_1_DIM_TABLE_2", press "Edit"
# and rename to: "DIM_TABLE_1_DIM_TABLE_2_z1Tl" or some other pattern that guarantees uniqueness.
# If you do not, you may see errors when Importing Table or Worksheet TML because the system cannot resolve JOIN names
# if there are duplicates
#

# Name of the Connection to be used as a Template, as seen in the UI
source_connection_name = os.getenv('source_connection_name')
# Name of the Connection to be used for all copied objects, as seen in the UI
destination_connection_name = os.getenv('destination_connection_name')

# To switch a connection, you'll also need the DB Name of the Connection (One Connection can allow multiple DBs, so
# this attribute exists in each Table and must be set)
destination_connection_db_name = os.getenv('destination_connection_db_name')

# Alternative way to copy content might look at Tags instead, or along with the Connection filter
source_tag_name = os.getenv('source_tag_name')

# Worksheet source tag name
ws_source_tag_name = os.getenv('ws_source_tag_name')

# Name of Tag to tag all newly copied content with
destination_tag_name = os.getenv('destination_tag_name')

# Group(s) to Share newly created objects with. Use 'Name" rather than "Display Name'
group_names_to_share_with = [os.getenv('group_names_to_share_with')]



#
# Get GUIDs from the names of the various items
#

# Get the Connection GUID of the Template Connection
source_conn_id = ts.connection.find_guid(name=source_connection_name)
print("Template connection ID", source_conn_id)

# Get the Connection GUID of the New Connection
destination_conn_id = ts.connection.find_guid(name=destination_connection_name)
print("New connection ID", destination_conn_id)


source_tag_id = ts.tag.find_guid(name=source_tag_name)
destination_tag_id = ts.tag.find_guid(name=destination_tag_name)

groups_to_share_with_guids = []
for g in group_names_to_share_with:
    group_guid = ts.group.find_guid(name=g)
    groups_to_share_with_guids.append(group_guid)
print(groups_to_share_with_guids)


def copy_tables(validate_instead_of_publish=True):

    # Get all of the tables for the Source Connection
    source_tables = ts.table.list_tables_for_connection(connection_guid=source_conn_id,
                                                        tags_filter=[source_tag_name])
    # Create a Mapping Dict Name : GUID for easy matching later
    source_connections_name_to_id_map = {}
    for t in source_tables:
        source_connections_name_to_id_map[t['name']] = t['id']
    print("All Tables from Source Connection")
    print(source_connections_name_to_id_map)

    # Get any Tables that already exist on the Destination Connection
    existing_tables_destination_connection = ts.table.list_tables_for_connection(connection_guid=destination_conn_id)
    destination_connection_existing_tables_name_to_id_map = {}
    for t in existing_tables_destination_connection:
        destination_connection_existing_tables_name_to_id_map[t['name']] = t['id']
    print("Destination Connection - Existing Tables")
    print(destination_connection_existing_tables_name_to_id_map)

    #
    # Next we grab the TML for each Source Table, make the updates to make the Destination, then Import to create new
    # This first round removes any JOIN details from each Table, so that they can be created in any order
    # without errors caused by references to Tables that do not yet exist for that Connection
    #

    # List to store GUIDs of newly created Tables
    new_table_guids = []
    # Loop to not attempt to recreate Tables that already exist (those will be updated in the second pass)
    for t in source_tables:
        if t['name'] in destination_connection_existing_tables_name_to_id_map:
            print('Table {} already exists on the New Connection, skipping'.format(t['name']))
            continue
        # The Table object is from the TML package. It is constructed with the Python Dict representation of the
        # TML coming out of the export_tml() method
        cur_table = Table(ts.tml.export_tml(guid=t['id']))
        # Print out original state of the TML to see if you like
        # print("TML in JSON of {}".format(t['id']))
        # print(json.dumps(cur_table.tml))

        #
        # Make any changes to the Table object to adjust to the new connection
        #

        # Change the Connection name to the New connection name
        cur_table.connection_name = destination_connection_name
        cur_table.db_name = destination_connection_db_name
        #cur_table.replace_connection_name_with_fqn(fqn_guid=destination_conn_id)
        # If you have any differences in naming, you can write additional rules here for mapping or adjustment
        # cur_table.content_name = "{}__{}".format(cur_table.content_name, destination_connection_db_name)

        #
        # VERY IMPORTANT STEP!
        # Remove any JOINs
        #
        cur_table.remove_joins()

        # If you are publishing New objects, you MUST remove the GUID from the TML for Import to work properly
        cur_table.remove_guid()

        # Print to see the final results to make sure the changes are what you want
        # print(json.dumps(cur_table.tml))

        # If desired, create a TML file on disk and export as YAML to really check against existing format
        # fh = open('export.tml', 'w', encoding='utf-8')
        # fh.write(yaml.dump(cur_table.tml))
        # fh.close()

        # Import is the "Publish" action. The validate_only flag lets you check that it will work and get the response
        # for what WILL happen, before actually running through and doing it
        response = ts.tml.import_tml(tml=cur_table.tml, create_new_on_server=True,
                                     validate_only=validate_instead_of_publish)

        print("Response from Import Action:")
        print(json.dumps(response))

        # When you actually want the new Table to publish, this section will run
        if validate_instead_of_publish is False:
            # Parse out the new GUID and add to the list of new ones
            new_obj_guid = ts.tml.get_guid_from_import_response(response=response)
            new_table_guids.append(new_obj_guid)
            print("New Table created with GUID {}".format(new_obj_guid))

    if validate_instead_of_publish is True:
        print("Full Process attempted and Validated")
    # If all you are doing is Validating, you can't do any of the next steps
    else:
        print("All Tables created, without JOINs")

        #
        # Tag the Newly Created Tables
        #

        if len(new_table_guids) > 0:
            print("Tagging the new tables")
            ts.table.assign_tags(object_guids=new_table_guids, tag_guids=[destination_tag_id])

        #
        # Add Sharing to the Newly Created Tables for Access Control
        #
        if len(new_table_guids) > 0:
            print("Sharing new tables with Specified Groups")
            permissions = ts.group.create_share_permissions(read_only_users_or_groups_guids=groups_to_share_with_guids)
            ts.table.share(object_guids=new_table_guids, permissions=permissions)


        # In second pass, we want to update all tables on Destination Connection, even those that alreay exist
        existing_tables_destination_connection = ts.table.list_tables_for_connection(connection_guid=destination_conn_id)
        destination_connection_existing_tables_name_to_id_map = {}
        for t in existing_tables_destination_connection:
            destination_connection_existing_tables_name_to_id_map[t['name']] = t['id']
        print("Destination Connection - All Tables")
        print(destination_connection_existing_tables_name_to_id_map)

        #
        # Second Publish - All Tables with JOINs to now existing Tables on Destination Connection
        #

        print("Republishing All Tables to Destination Connection with JOINs")
        success_count = 0
        error_count = 0
        error_responses = []
        for t in source_tables:
            cur_table = Table(ts.tml.export_tml(guid=t['id']))
            # print("TML in JSON of {}".format(t['id']))
            # print(json.dumps(cur_table.tml))

            # Make the same change to the TML as done in the first round
            cur_table.connection_name = destination_connection_name
            cur_table.db_name = destination_connection_db_name

            # Get the GUID of the Table with the same name on the Destination connection,
            # and update the Table GUID property.
            # This is what tells the Import process which object on the Server to update
            new_table_guid = destination_connection_existing_tables_name_to_id_map[t['name']]
            cur_table.guid = new_table_guid

            # All of the Tables referenced in the JOINs section will come down with just Table Names
            # But since there are multiple Tables on the Server with the same name, you must specify a GUID
            # as the FQN, so that the Import process will know which Table to map to
            # This updates any Table in the JOINs with the appropriate FQNs from the Name: GUID mapping Dict
            cur_table.remap_joins_to_new_fqn(name_to_fqn_map=destination_connection_existing_tables_name_to_id_map)

            # The JOINs themselves need to be named uniquely. This adds a random alphanumeric of 6 characters to the end
            cur_table.randomize_join_names()

            # print("Updated TML in JSON of {}".format(t['id']))
            #rint(json.dumps(cur_table.tml))

            # Import to Server, with create_new_on_server False and the correct GUID to update the new Dest Table
            response = ts.tml.import_tml(tml=cur_table.tml, create_new_on_server=False, validate_only=False)

            print("Response from Import: ")
            print(response)
            was_success = ts.tml.did_import_succeed(response=response)
            if was_success:
                success_count += 1
            else:
                error_count += 1
                error_responses.append(response)

        print("{} successful, {} failures".format(success_count, error_count))

        if error_count > 0:
            print("Errors encountered:")
            print(error_responses)


# Tables can exist with the same name (and in this process, we intend that to happen)
# So it is necessary to find the Tables that attach to the Destination Connection,
# create a mapping of Name: GUID, and then use the GUIDs so the those Tables will be used in the Import process
def copy_worksheets(validate_instead_of_publish=True, lineage_file=None):
    # You'll need to find the set of Worksheets you want to copy
    # This might be a specific name, or a Tag, or a set of Tags
    # It's more complex to find the Worksheets connected to a particular Connection, since that is mediated through
    # the Tables
    search_term_for_source_worksheets = os.getenv('source_tag_name')
    tag_for_source_worksheets = ''

    worksheets = ts.worksheet.list(filter="%{}%".format(search_term_for_source_worksheets))
    # You might do additional filtering here to pull out a more specific set of worksheets
    print(worksheets)

    # Starting in July Cloud, you can do the following:
    # Get the Tables from the Source Connection
    # source_tables = ts.table.list_tables_for_connection(connection_guid=source_conn_id,
    #                                                     tags_filter=[source_tag_name])
    # Get all the Worksheets that connect to those Tables
    # The same Worksheet will be listed many times, possibly for each table, so we use Dict to reduce on ID
    #all_worksheets_id_name_map = {}
    #for t in source_tables:
    #    dependent_worksheets = ts.table.get_dependent_worksheets_for_table(table_guid=t['id'])
    #
    #    for ws in dependent_worksheets:
    #        all_worksheets_id_name_map[ws['id']] = ws['name']
    # print(all_worksheets_id_name_map)


    # Get all of the Tables on the Destination Connection
    destination_connection_existing_tables = ts.table.list_tables_for_connection(connection_guid=destination_conn_id)
    destination_connection_existing_tables_name_to_id_map = {}
    for t in destination_connection_existing_tables:
        destination_connection_existing_tables_name_to_id_map[t['name']] = t['id']
    print("Destination Connection - Existing Tables")
    print(destination_connection_existing_tables_name_to_id_map)

    success_count = 0
    error_count = 0
    error_responses = []
    new_guids = []
    for w in worksheets:
        cur_ws = Worksheet(ts.tml.export_tml(guid=w['id']))
        # print("TML in JSON of {}".format(w['id']))
        # print(json.dumps(cur_ws.tml))

        # Find any Table names and substitute in the GUID as FQN for that Table Name on the Destination Connection
        cur_ws.remap_tables_to_new_fqn(name_to_fqn_map=destination_connection_existing_tables_name_to_id_map)

        #
        # Important step! You must remove GUID to create a new object successfully on Server!
        #
        cur_ws.remove_guid()

        # Print the update if you want to see
        print("Updated TML {}".format(w['id']))
        print(json.dumps(cur_ws.tml))

        response = ts.tml.import_tml(tml=cur_ws.tml, create_new_on_server=True,
                                     validate_only=validate_instead_of_publish)

        print("Response from import:")
        print(response)
        # When you actually want the new Table to publish, this section will run
        if validate_instead_of_publish is False:
            was_success = ts.tml.did_import_succeed(response=response)
            if was_success:
                success_count += 1
                new_guid = ts.tml.get_guid_from_import_response(response=response)
                print("New Worksheet created with GUID {}".format(new_guid))
                new_guids.append(new_guid)
            else:
                error_count += 1
                error_responses.append(response)

    if validate_instead_of_publish is True:
        print("Full Process attempted and Validated")
    # If all you are doing is Validating, you can't do any of the next steps
    else:
        print("{} successful, {} failures".format(success_count, error_count))

        print("Assigning tags to new Worksheets")
        ts.worksheet.assign_tags(object_guids=new_guids, tag_guids=[destination_tag_id])


def copy_pinboards(validate_instead_of_publish=True):
    # Find pinboards. In this case we use a tag filter, assuming we've followed already done this action
    pbs = ts.pinboard.list(tags_filter=[ws_source_tag_name])

    print(pbs)
    # Adjust their Worksheets (only worksheets, Pinboard should not connect just to Table)

    # Again here we are using the Tag filter to get the worksheets that we have tagged
    # It may be possible to do this with the new /dependency endpoints in July Cloud release
    worksheets_for_destination = ts.worksheet.list(tags_filter=[destination_tag_name])
    destination_worksheets_name_to_id_map = {}
    for w in worksheets_for_destination:
        destination_worksheets_name_to_id_map[w['name']] = w['id']

    success_count = 0
    error_count = 0
    error_responses = []
    new_guids = []
    for pb in pbs:
        cur_pb = Pinboard(ts.tml.export_tml(guid=pb['id']))
        print("TML in JSON of {}".format(pb['id']))
        print(json.dumps(cur_pb.tml))

        # Find any Table names and substitute in the GUID as FQN for that Table Name on the Destination Connection
        cur_pb.remap_worksheets_to_new_fqn(name_to_guid_map=destination_worksheets_name_to_id_map)

        #
        # Important step! You must remove GUID to create a new object successfully on Server!
        #
        cur_pb.remove_guid()

        # Print the update if you want to see
        print("Updated TML {}".format(pb['id']))
        print(json.dumps(cur_pb.tml))

        response = ts.tml.import_tml(tml=cur_pb.tml, create_new_on_server=True,
                                     validate_only=validate_instead_of_publish)
        print("Response from import:")
        print(response)
        # When you actually want the new Table to publish, this section will run
        if validate_instead_of_publish is False:
            was_success = ts.tml.did_import_succeed(response=response)
            print("Was Import succcessful?", was_success)
            if was_success:
                success_count += 1
                # Parse out the new GUID and add to the list of new ones
                new_guid = ts.tml.get_guid_from_import_response(response=response)
                print("New Pinboard created with GUID {}".format(new_guid))
                new_guids.append(new_guid)
            else:
                error_count += 1
                error_responses.append(response)

    if validate_instead_of_publish is True:
        print("Full Process attempted and Validated")
    # If all you are doing is Validating, you can't do any of the next steps
    else:
        print("{} successful, {} failures".format(success_count, error_count))

        print("Assigning tags to new Pinboards")
        ts.pinboard.assign_tags(object_guids=new_guids, tag_guids=[destination_tag_id])


def copy_answers(validate_instead_of_publish=True):
    # Find pinboards. In this case we use a tag filter, assuming we've followed already done this action
    answers = ts.answer.list(tags_filter=[ws_source_tag_name])

    print(answers)
    # Adjust their Worksheets (only worksheets, Answer should not connect just to Table)

    # Again here we are using the Tag filter to get the worksheets that we have tagged
    # It may be possible to do this with the new /dependency endpoints in July Cloud release
    worksheets_for_destination = ts.worksheet.list(tags_filter=[destination_tag_name])
    destination_worksheets_name_to_id_map = {}
    for w in worksheets_for_destination:
        destination_worksheets_name_to_id_map[w['name']] = w['id']

    success_count = 0
    error_count = 0
    error_responses = []
    new_guids = []
    for a in answers:
        cur_answer = Pinboard(ts.tml.export_tml(guid=a['id']))
        print("TML in JSON of {}".format(a['id']))
        print(json.dumps(cur_answer.tml))

        # Find any Table names and substitute in the GUID as FQN for that Table Name on the Destination Connection
        cur_answer.remap_worksheets_to_new_fqn(name_to_guid_map=destination_worksheets_name_to_id_map)

        #
        # Important step! You must remove GUID to create a new object successfully on Server!
        #
        cur_answer.remove_guid()

        # Print the update if you want to see
        print("Updated TML {}".format(a['id']))
        print(json.dumps(cur_answer.tml))

        response = ts.tml.import_tml(tml=cur_answer.tml, create_new_on_server=True,
                                     validate_only=validate_instead_of_publish)
        print("Response from import:")
        print(response)
        # When you actually want the new Table to publish, this section will run
        if validate_instead_of_publish is False:
            was_success = ts.tml.did_import_succeed(response=response)
            print("Was Import succcessful?", was_success)
            if was_success:
                success_count += 1
                # Parse out the new GUID and add to the list of new ones
                new_guid = ts.tml.get_guid_from_import_response(response=response)
                print("New Answer created with GUID {}".format(new_guid))
                new_guids.append(new_guid)
            else:
                error_count += 1
                error_responses.append(response)

    if validate_instead_of_publish is True:
        print("Full Process attempted and Validated")
    # If all you are doing is Validating, you can't do any of the next steps
    else:
        print("{} successful, {} failures".format(success_count, error_count))

        print("Assigning tags to new Answers")
        ts.pinboard.assign_tags(object_guids=new_guids, tag_guids=[destination_tag_id])


def add_sharing_to_tables():
    # Get any Tables that already exist on the Destination Connection
    existing_tables_destination_connection = ts.table.list_tables_for_connection(connection_guid=destination_conn_id)
    destination_connection_existing_tables_name_to_id_map = {}
    for t in existing_tables_destination_connection:
        destination_connection_existing_tables_name_to_id_map[t['name']] = t['id']
    print("Destination Connection - Existing Tables")
    print(destination_connection_existing_tables_name_to_id_map)
    #
    # Add Sharing to the Newly Created Tables for Access Control
    #
    if len(destination_connection_existing_tables_name_to_id_map) > 0:
        table_guids = list(destination_connection_existing_tables_name_to_id_map.values())
        print("Sharing new tables with Specified Groups")
        permissions = ts.group.create_share_permissions(read_only_users_or_groups_guids=groups_to_share_with_guids)
        ts.table.share(object_guids=table_guids, permissions=permissions)


# Lineage Tracking
# You probably want to track which objects are created from which template objects, as this can be very useful later
# when making updates (and given name duplication, may be hard to determine later)

# Lineage tracking file
lineage_filename = '../lineage.json'

with open(lineage_filename, 'r+') as lineage_fh:
    copy_tables(validate_instead_of_publish=False)
    #copy_worksheets(validate_instead_of_publish=True)
    # copy_pinboards(validate_instead_of_publish=True)
    # copy_answers(validate_instead_of_publish=True)
    # add_sharing_to_tables()