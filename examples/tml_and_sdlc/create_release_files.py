import os
import json
import requests.exceptions
import sys, getopt
from typing import List, Dict
import getpass
import base64

from thoughtspot_rest_api_v1 import MetadataNames, MetadataSubtypes
from thoughtspot_tml import *

# TOML config file for sharing settings between deployment scripts
# You may want something more secure to protect admin level credentials, particularly password
import toml
config_file = 'thoughtspot_release_config.toml'

#
# STEP 2 SDLC Process
# create_release_files.py is a command-line script to copy and modify downloaded TML files to create a new 'release
# The purpose is to transform 'dev' objects in source-control directory to
# New files maintain original filenames from source: {releases directory}/{release name}/{object_type}/{dev_GUID}.{object_type}.tml
# There is a parent_child_guid_map file built by the 'import_release_files.py' script which is used to substitute
# GUIDs in for the 'destination environment'
# Existing files on disk in the destination directory will be overwritten completely when this is run
#

username = ""
password = ""
server = ""
# This is the root directory, and then we have sub-directories for Pinboards, Answers, etc.
# for organizational purposes
# Needs to be fully qualified with trailing slash. MacOs example: /Users/{username}/Documents/thoughtspot_tml/
orig_git_root_directory = ""
releases_root_directory = ""

parent_child_guid_map = {}
#
# Parent:Child GUID map
#

#
# Example store format on disk is structured:
# { 'destination_environment_name' :
#   { 'dev_guid' : 'env_guid' }
# }
#
destination_env_name = 'prod'


def load_config(environment_name, new_password=False):
    save_password = None
    with open(config_file, 'r', encoding='utf-8') as cfh:
        global server
        global orig_git_root_directory
        global releases_root_directory
        global destination_env_name
        global username
        global password
        global parent_child_guid_map

        destination_env_name = environment_name

        parsed_toml = toml.loads(cfh.read())
        server = parsed_toml['server']
        orig_git_root_directory = parsed_toml['git_directory']
        releases_root_directory = parsed_toml['releases_directory']
        username = parsed_toml['username']

        #
        # Replace with other secure form of password retrieval if needed
        #
        if parsed_toml['password_do_not_enter_manually'] == "" or new_password is True:
            password = getpass.getpass("Please enter ThoughtSpot password on {} for configured username {}: ".format(server, username))
            # Ask about saving password
            while save_password is None:
                save_password_input = input("Save password to config file? Y/n: ")
                if save_password_input.lower() == 'y':
                    save_password = True
                    # Write encoded to TOML file at end
                elif save_password_input.lower == 'n':
                    save_password = False
        else:
            e_pw = parsed_toml['password_do_not_enter_manually']
            d_pw = base64.standard_b64decode(e_pw)
            password = d_pw.decode(encoding='utf-8')
    if save_password is True:
        print("Saving password encoded to config file...")
        bytes_pw = password.encode(encoding='utf-8')
        e_pw = base64.standard_b64encode(bytes_pw)
        parsed_toml['password_do_not_enter_manually'] = str(e_pw, encoding='ascii')
        with open(config_file, 'w', encoding='utf-8') as cfh:
            cfh.write(toml.dumps(parsed_toml))

    # Parent:Child GUID map loading
    parent_child_guid_map_json_file = parsed_toml['parent_child_guid_map_file']
    if os.path.exists(parent_child_guid_map_json_file) is False:
        parent_child_obj_guid_map = {environment_name: {}}
        with open(parent_child_guid_map_json_file, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps(parent_child_obj_guid_map, indent=2))
    else:
        parent_child_guid_map = json.load(open(parent_child_guid_map_json_file, 'r'))

    if environment_name in parent_child_guid_map:
        print("Mapping for environments")
        print(parent_child_guid_map[environment_name])
    else:
        parent_child_guid_map[environment_name] = {}

#
# To create a "release", we'll parse through all the files in the originating "dev" branch directory, then
# make copies to the "release" directory
#

#
# The most standard case of 'promoting to new environment' switches the Connection details in the Tables
#
#

#
# TABLE object type transformations
#

# Tables contain details relating to the actual data source - Connection Name, Schema, Database, db_table_name
# Other object types only need to have their GUID/fqn values swapped from 'dev' object values to the new environment

#
# This is an example function to show the different things you might do to change connection / database details
# In a simple use case, you may just be changing from one Connection to another with same database / schema names
# This shows the possibility of having several different named connections in each environment
# The most complex form would have variations in Connection / Schema / DB Name for each tenant environment
# Example is patterned on a Snowflake based example, so the properties might vary some on different data source type
#
def connection_details_changes(table_obj: Table):

    connection_name_map = {
        'Original Connection 1': 'Final Connection 1',
        'Original Connection 2': 'Final Connection 2',
        # 'Bryant Snowflake': 'Bryant Snowflake PROD'   # embed-1
        'Bryant Snowflake': 'Snowflake - Bryant 1'
    }
    # Only replace connection name if in the mapping
    if table_obj.connection_name in connection_name_map.keys():
        table_obj.connection_name = connection_name_map[table_obj.connection_name]

    # You can do a similar pattern with finding and replacing schema and db_name, or even db_table using syntax below:

    # table_obj.schema = new_schema
    # table_obj.db_name = new_db_name
    # table_obj.db_table = new_db_table

    return table_obj


#
# GUID / FQN remapping
#

#
# There must be a mapping dictionary of Parent GUID (the GUIDs of the 'dev' branch) with 'child GUID',
# the GUID representing the object in the branch / environment we are publishing to.
# If the child GUID does not exist for a Parent GUID, then it is a new object to be published,
# and the new child GUID must be recorded in the mapping for any future updates or references in
# descendant objects
#
def child_guid_replacement(obj: TML, guid_map: Dict):
    # If there is an existing child object, swap in the GUID to allow for update
    if obj.guid in guid_map.keys():
        obj.guid = guid_map[obj.guid]
    # If there is no existing child object, then it is a "create new" situation
    else:
        obj.remove_guid()

    # Look into any 'tables' section and replace any FQNs that might be present (all non-Table objects)
    obj.replace_fqns_from_map(parent_child_guid_map=guid_map)
    return obj


# Mapping of the metadata object types to the directory to save them to
object_type_directory_map = {
    MetadataNames.LIVEBOARD: 'liveboard',
    MetadataNames.ANSWER: 'answer',
    MetadataSubtypes.TABLE: 'table',
    MetadataSubtypes.WORKSHEET: 'worksheet',
    MetadataSubtypes.VIEW: 'view'
}

# Mapping of the metadata object types to the directory to save them to
plain_name_object_type_map = {
    'liveboard' : MetadataNames.LIVEBOARD,
    'answer':  MetadataNames.ANSWER,
    'table': MetadataSubtypes.TABLE,
    'worksheet': MetadataSubtypes.WORKSHEET,
    'view': MetadataSubtypes.VIEW
}


def copy_objects_to_release_directory(source_dir, release_dir, parent_child_obj_guid_map, object_type):
    dir_list = os.listdir(source_dir)
    for filename in dir_list:
        if filename.find('.tml') != -1:
            print("Copying {}".format(filename))
            with open(source_dir + "/" + filename, 'r', encoding='utf-8') as fh:
                yaml_od = YAMLTML.load_string(fh.read())
                # Tables have their own set of transformations
                if object_type == 'table':
                    table_obj = Table(yaml_od)

                    # Only copying from one connection for demo
                    if table_obj.connection_name == 'Bryant Snowflake':
                        # Any transformations you need to make implemented in these functions (or additional you make)
                        connection_details_changes(table_obj)
                        child_guid_replacement(obj=table_obj, guid_map=parent_child_obj_guid_map)

                        with open(release_dir + filename, 'w', encoding='utf-8') as fh2:
                            fh2.write(YAMLTML.dump_tml_object(table_obj))
                # All other object types, replace object GUID and any FQN properties found in 'tables' section
                else:
                    obj = TML(yaml_od)
                    child_guid_replacement(obj=obj, guid_map=parent_child_obj_guid_map)

                    with open(release_dir + filename, 'w', encoding='utf-8') as fh2:
                        fh2.write(YAMLTML.dump_tml_object(table_obj))


def main(argv):
    global destination_env_name
    new_password = False
    try:
        opts, args = getopt.getopt(argv, "hpe:", ["password_reset"])
    except getopt.GetoptError:

        print("create_release_files.py [--password_reset] -e <environment-name> <release-name>")
        print("Will create directories if they do not exist")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("create_release_files.py [--password_reset] -e <environment-name> <release-name>")
            print("Will create directories if they do not exist")
            sys.exit()
        elif opt in ['-p', '--password_reset']:
            new_password = True
        elif opt == '-e':
            destination_env_name = arg
    load_config(environment_name=destination_env_name, new_password=new_password)
    parent_child_guid_map_env = parent_child_guid_map[destination_env_name]

    release_directory = args[0]
    release_full_directory = "{}/{}/{}/".format(releases_root_directory, args[0],
                                                object_type_directory_map[MetadataSubtypes.TABLE])
    print("Building release named {} to environment destination: {} ".format(release_directory, destination_env_name))
    print("Files for release will be saved to: {}".format(release_full_directory))
    if os.path.exists(release_full_directory) is False:
        print("Creating the path to: {}".format(release_full_directory))
        os.makedirs(release_full_directory)

    copy_objects_to_release_directory(source_dir=orig_git_root_directory + "/" + object_type_directory_map[MetadataSubtypes.TABLE],
                                      release_dir=release_full_directory,
                                      parent_child_obj_guid_map=parent_child_guid_map_env)


if __name__ == "__main__":
   main(sys.argv[1:])