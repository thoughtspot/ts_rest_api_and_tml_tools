import os
import json
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

#
# GLOBAL VARIABLES
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

table_properties_map = {}
#
# END GLOBAL VARIABLES
#


# All of the scripts share a TOML config file. This function sets all the global vars based on the config
# new_password=True triggers the password reset flow which stores the password encoded (not encrypted!)
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
        global table_properties_map

        destination_env_name = environment_name

        parsed_toml = toml.loads(cfh.read())
        server = parsed_toml["thoughtspot_instances"][environment_name]['server']
        orig_git_root_directory = parsed_toml['git_directory']
        releases_root_directory = parsed_toml['releases_directory']
        username = parsed_toml["thoughtspot_instances"][environment_name]['username']

        table_properties_map = parsed_toml["table_properties_map"]

        #
        # Replace with other secure form of password retrieval if needed
        #
        if parsed_toml["thoughtspot_instances"][environment_name]['password_do_not_enter_manually'] == "" or new_password is True:
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
            e_pw = parsed_toml["thoughtspot_instances"][environment_name]['password_do_not_enter_manually']
            d_pw = base64.standard_b64decode(e_pw)
            password = d_pw.decode(encoding='utf-8')
    if save_password is True:
        print("Saving password encoded to config file...")
        bytes_pw = password.encode(encoding='utf-8')
        e_pw = base64.standard_b64encode(bytes_pw)
        parsed_toml["thoughtspot_instances"][environment_name]['password_do_not_enter_manually'] = str(e_pw, encoding='ascii')
        with open(config_file, 'w', encoding='utf-8') as cfh:
            cfh.write(toml.dumps(parsed_toml))

    # Parent:Child GUID map loading
    # To be able to update objects in another environment, we store a mapping of the "child guid" created from the
    # publishing of an object from the 'dev' environment, which becomes the 'parent guid'
    # This creates the JSON file for the mappings if it does not exist already
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
# then swapping all of the GUIDs in the FQN properties for all other object types
#
#

#
# TABLE object type transformations
#


# Tables contain details relating to the actual data source - Connection Name, Schema, Database, db_table_name
# Other object types only need to have their GUID/fqn values swapped from 'dev' object values to the new environment

#
# The mapping format allows for specifying {Connection Name}.{Database}.{Schema}.{db_table_name} matches for replacement
# As long as the key and values go to the same level of depth, you can specify at any level what you would like to do
#
def all_table_properties_changes(table_obj: Table):

    if destination_env_name not in table_properties_map.keys():
        print("No Table Properties Mapping exists in TOML config for environment '{}'".format(destination_env_name))
    env_map = table_properties_map[destination_env_name]
    # Validate the table_properties_map : do all keys and values have the same depth of specification?
    specification_depth = None
    for k in env_map:
        key_len = len(k.split("."))
        val_len = len(env_map[k].split("."))
        if key_len != val_len:
            print("All table properties keys and values must have the same depth of specification")
            print("{} and {} do not have the same depth, one specifies further than the other".format(k, env_map[k]))
            print("Please correct in the configuration TOML file and re-run")
            print("Exiting...")
            exit()
        # Set the specification depth
        if specification_depth is None:
            specification_depth = key_len
            if key_len > 4:
                print("Depth of specification cannot exceed 4 - {Connection Name}.{Database}.{Schema}.{db_table_name}")
                print("Please correct in the configuration TOML file and re-run")
                print("Exiting...")
                exit()
        # Check that all entries have the same depth of specification
        else:
            if key_len != specification_depth:
                print("All entries in the table properties map must have same depth of specification")
                print("Check the mapping in the configuration TOML file and correct:")
                print(json.dumps(table_properties_map, indent=2))
                print("Exiting...")
                exit()
    # Connection Name
    if specification_depth == 1:
        if table_obj.connection_name in env_map.keys():
            table_obj.connection_name = env_map[table_obj.connection_name]
    # Connection Name.Database
    elif specification_depth == 2:
        combined_key = "{}.{}".format(table_obj.connection_name, table_obj.db_name)
        if combined_key in env_map.keys():
            table_obj.connection_name = env_map[combined_key].split(".")[0]
            table_obj.db_name = env_map[combined_key].split(".")[1]
    # Connection Name.Database.Schema
    elif specification_depth == 3:
        combined_key = "{}.{}.{}".format(table_obj.connection_name, table_obj.db_name, table_obj.schema)
        if combined_key in env_map.keys():
            table_obj.connection_name = env_map[combined_key].split(".")[0]
            table_obj.db_name = env_map[combined_key].split(".")[1]
            table_obj.schema = env_map[combined_key].split(".")[2]
    # Connection Name.Database.Schema.DB Table Name
    elif specification_depth == 4:
        combined_key = "{}.{}.{}.{}".format(table_obj.connection_name, table_obj.db_name,
                                            table_obj.schema, table_obj.db_table)
        if combined_key in env_map.keys():
            table_obj.connection_name = env_map[combined_key].split(".")[0]
            table_obj.db_name = env_map[combined_key].split(".")[1]
            table_obj.schema = env_map[combined_key].split(".")[2]
            table_obj.db_table = env_map[combined_key].split(".")[3]

    return table_obj
#
# END TABLE object transformations
#

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
    try:
        obj.replace_fqns_from_map(parent_child_guid_map=guid_map)
        return obj
    except IndexError as e:
        print(e)
        print("Cannot complete release build without a mapped GUID for referenced object")
        print("Please publish all of the objects of previous levels in the object hierarchy")
        print("The order to publish objects is: table, view, worksheet, answer/liveboard")
        print("Exiting, please clean-up any files generated up to this point")
        exit()


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


#
# Function that actually copies the original TML files, doing the necessary changes to adjust to the next environment
# Tables are parsed differently than the other objects as they have a different set of transformations to adjust
# the connection details contained within the Table object.
# Tables are also split into sub-directories based on shared Connection Name, which allows for grouping to IMPORT
#
def copy_objects_to_release_directory(source_dir, release_dir, parent_child_obj_guid_map, object_type,
                                      split_tables_by_conn=True):
    dir_list = os.listdir(source_dir)
    for filename in dir_list:
        # Skip anything that doesn't end in .tml
        if filename.find('.tml') != -1:
            print("Copying {}".format(filename))
            with open(source_dir + "/" + filename, 'r', encoding='utf-8') as fh:
                yaml_od = YAMLTML.load_string(fh.read())
                # Tables have their own set of transformations
                if object_type == 'table':
                    obj = Table(yaml_od)

                    # Transforms table details (connection name, database, schema, table name)
                    all_table_properties_changes(obj)

                    # Implement any other transformations to able files (add RLS rules etc.) here

                    # This only swaps the object GUID (it's own identifier) for a Table
                    child_guid_replacement(obj=obj, guid_map=parent_child_obj_guid_map)

                    # Tables get split into directories by Connection Name (using the final connection name)
                    if split_tables_by_conn is True:
                        if obj.connection_name is None:
                            final_filename = release_dir + filename
                        else:
                            connection_dir_name = str(obj.connection_name).replace(" ", "_")
                            final_table_dir = release_dir + connection_dir_name + "/"
                            # Create directory is doesn't exist
                            if os.path.exists(final_table_dir) is False:
                                print("Creating the path to: {}".format(final_table_dir))
                                os.makedirs(final_table_dir)

                            final_filename = final_table_dir + filename
                    else:
                        final_filename = release_dir + filename
                    with open(final_filename, 'w', encoding='utf-8') as fh2:
                        fh2.write(YAMLTML.dump_tml_object(obj))

                # All other object types, just parse as TML, swap any GUIDs for the new environment, write to directory
                else:
                    # Generic TML class has enough methods to run this without specific object class
                    obj = TML(yaml_od)
                    # Swaps the object GUID (it's own identifier) and any GUIDs in an 'fqn' property under the 'tables'
                    # property
                    child_guid_replacement(obj=obj, guid_map=parent_child_obj_guid_map)

                    with open(release_dir + filename, 'w', encoding='utf-8') as fh2:
                        fh2.write(YAMLTML.dump_tml_object(obj))


#
# Command-line argument parsing for the script
#
def main(argv):
    global destination_env_name
    new_password = False
    object_type = None
    try:
        opts, args = getopt.getopt(argv, "hpc:o:e:", ["password_reset", "config_file=", "object_type="])
    except getopt.GetoptError:

        print("create_release_files.py [--password_reset] [--config_file <alt_config.toml>] -o <object_type> -e <environment-name> <release-name>")
        print("object_type can be: liveboard, answer, table, worksheet, view")
        print("Will create directories if they do not exist")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("create_release_files.py [--password_reset] -o <object_type> -e <environment-name> <release-name>")
            print("object_type can be: liveboard, answer, table, worksheet, view")
            print("Will create directories if they do not exist")
            sys.exit()
        elif opt in ['-p', '--password_reset']:
            new_password = True
        # Allows using an alternative TOML config file from the default
        elif opt in ("-c", "--config_file"):
            global config_file
            config_file = arg
        elif opt in ['-o', '--object_type']:
            object_type = arg
        elif opt == '-e':
            destination_env_name = arg

    load_config(environment_name=destination_env_name, new_password=new_password)
    parent_child_guid_map_env = parent_child_guid_map[destination_env_name]

    release_directory = args[0]
    if object_type not in ["liveboard", "answer", "table", "worksheet", "view"]:
        print("Must include -o or --object_type argument with value: liveboard, answer, table, worksheet, view")
        print("Exiting...")
        exit()
    print("Creating release files for {} type to environment {} with name {}".format(object_type,
                                                                                     destination_env_name,
                                                                                     release_directory))
    release_full_directory = "{}/{}/{}/".format(releases_root_directory, args[0],
                                                object_type_directory_map[plain_name_object_type_map[object_type]])
    print("Building release named {} to environment destination: {} ".format(release_directory, destination_env_name))
    print("Files for release will be saved to: {}".format(release_full_directory))
    if os.path.exists(release_full_directory) is False:
        print("Creating the path to: {}".format(release_full_directory))
        os.makedirs(release_full_directory)

    copy_objects_to_release_directory(source_dir=orig_git_root_directory + "/" + object_type_directory_map[plain_name_object_type_map[object_type]],
                                      release_dir=release_full_directory,
                                      parent_child_obj_guid_map=parent_child_guid_map_env,
                                      object_type=object_type)


if __name__ == "__main__":
   main(sys.argv[1:])