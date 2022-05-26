#!/usr/bin/env python3

import os
import json
import requests.exceptions
import sys, getopt
from typing import List, Dict
import getpass
import base64

from thoughtspot_rest_api_v1 import TSRestApiV1, MetadataNames, MetadataSubtypes

# TOML config file for sharing settings between deployment scripts
# You may want something more secure to protect admin level credentials, particularly password
import toml
config_file = 'thoughtspot_release_config.toml'

#
# STEP 3 SDLC Process
# import_release_files.py is a command-line script to import the TML files created for a 'release' to a ThoughtSpot instance
# When new objects are created, the parent_child_guid_map file is updated to map the 'parent' GUID with the new 'child' GUID
# This process depends on keeping the filenames the same from the dev environment, so they can be trusted as the 'parent' GUID
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
parent_child_guid_map_json_file = ""
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

connection_name_map = {}
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
        global parent_child_guid_map_json_file
        global connection_name_map

        destination_env_name = environment_name

        parsed_toml = toml.loads(cfh.read())
        server = parsed_toml["thoughtspot_instances"][environment_name]['server']
        orig_git_root_directory = parsed_toml['git_directory']
        releases_root_directory = parsed_toml['releases_directory']
        username = parsed_toml["thoughtspot_instances"][environment_name]['username']

        connection_name_map = parsed_toml["connection_name_map"]

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
# Function that parses through the release directories of TML files and imports them using Import TML
# Tables are imported together by sub-directory (which are split by Connection Name in 'create_release_files.py' )
#
def import_objects_from_release_directory(release_dir):
    # Create and login to REST API using the global variables set by the load_config() function
    ts: TSRestApiV1 = TSRestApiV1(server_url=server)
    try:
        ts.session_login(username=username, password=password)
    except requests.exceptions.HTTPError as e:
        print("Unable to sign-in with REST API session with following errors:")
        print(e)
        print(e.response.content)
        print("Exiting script...")
        exit()

    print("Signed into {}".format(server))

    dir_list = os.listdir(release_dir)
    import_guids = []
    import_tml_strs = []
    new_parent_child_guid_map = {}

    directories_to_publish_from = [release_dir]
    # Look for sub-directories of tables to import each as a package
    for filename in dir_list:
        full_filepath = os.path.join(release_dir, filename)
        # If tables, look at sub-directories per Connection and publish each separately (related objects published together)
        if os.path.isdir(full_filepath):
            print("Found a sub-directory of tables")
            print(full_filepath)
            directories_to_publish_from.append(full_filepath)
    # Go through each directory that was found (should only be 1 except for Tables)
    for d in directories_to_publish_from:
        dir_list_2 = os.listdir(d)
        print("Publishing all TML content in {} as a single package".format(d))
        # Parse every TML file, add to list to be imported
        for filename in dir_list_2:
            if filename.find('.tml') != -1:
                print("Importing {}".format(filename))
                with open(d + "/" + filename, 'r', encoding='utf-8') as fh:
                    # File naming pattern is {guid}.{object_type}.tml
                    parent_guid = filename.split('.')[0]
                    import_guids.append(parent_guid)
                    # Import as YAML strs directly in array
                    import_tml_strs.append(fh.read())
                    # table_obj = Table(yaml_od)
        # Skip to next if directory is blank
        if len(import_guids) == 0:
            continue

        print('Importing the following objects with parent GUIDS {}'.format(import_guids))
        # Publish all of the TML strings together
        try:
            results = ts.metadata_tml_import(import_tml_strs, create_new_on_server=False)
            print(results)
            guids_from_import = ts.guids_from_imported_tml(results)
            # Run through the originating GUID (parent) and map the new GUID (child) - they should be in same order
            i = 0
            for guid in import_guids:
                new_parent_child_guid_map[guid] = guids_from_import[i]
                i += 1
            return new_parent_child_guid_map
        except requests.exceptions.HTTPError as e:
            print(e)
            print(e.response.content)
            print(e.response.request.url)
            with open('../examples/tml_and_sdlc/import_error.log', 'w', encoding='utf-8') as efh:
                efh.write(e.response.request.body)
            print("Exiting after failure...")
            exit()
        # TML Import can return a 200 with a JSON response indicating the status of TML parsing, which can have Errors
        # This raises a SyntaxError, which can then be parsed as such:
        except SyntaxError as e:
            print('TML import encountered error:')
            print(e)
            with open('../examples/tml_and_sdlc/import_error.log', 'w', encoding='utf-8') as efh:
                efh.write(str(e))
            # SyntaxError is actually returning the List of errors (from the JSON return
            i = 0
            for a in e.msg:
                # Only print if there is a non-OK response i.e. an error
                if a['response']['status']['status_code'] != 'OK':
                    print("Error report for imported file {}".format(import_guids[i]))
                    print(a)
                    # 'error_code': 14501, 'error_message': 'Logical table ID to update is compulsory for UPDATE action.'
                    if a['response']['status']["error_code"] == 14501:
                        print("Error 14501 indicates that another Table object exists already connected to the same table in the database on this connection")
                    else:
                        print("Exiting after failure to import...")
                        exit()
                i += 1

#
# Command-line argument parsing for the script
#
def main(argv):
    global destination_env_name
    new_password = False
    object_type = None
    connection_name_arg = None
    try:
        opts, args = getopt.getopt(argv, "hpc:d:o:e:", ["password_reset", "object_type="])
    except getopt.GetoptError:

        print("import_release_files.py [--password_reset] [--config_file <alt_config.toml>] [-d <connection name_subdirectory>] -o <object_type> -e <environment-name> <release-name>")
        print("object_type can be: liveboard, answer, table, worksheet, view")
        print("Will create directories if they do not exist")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("import_release_files.py [--password_reset] [-d <connection name_subdirectory>] -o <object_type> -e <environment-name> <release-name>")
            print("object_type can be: liveboard, answer, table, worksheet, view")
            print("Will create directories if they do not exist")
            sys.exit()
        elif opt in ['-p', '--password_reset']:
            new_password = True
        # Allows using an alternative TOML config file from the default
        elif opt in ("-c", "--config_file"):
            global config_file
            config_file = arg
        # Specific Connection Name for tables if you just want to publish that one
        elif opt in ['-d', "--connection_name_subdirectory"]:
            connection_name_arg = arg
        elif opt in ['-o', '--object_type']:
            object_type = arg
        elif opt == '-e':
            destination_env_name = arg

    load_config(environment_name=destination_env_name, new_password=new_password)
    # parent_child_guid_map_env = parent_child_guid_map[destination_env_name]

    release_directory = args[0]
    if object_type not in ["liveboard", "answer", "table", "worksheet", "view"]:
        print("Must include -o or --object_type argument with value: liveboard, answer, table, worksheet, view")
        print("Exiting...")
        exit()
    print("Creating release files for {} type to environment {} with name {}".format(object_type,
                                                                                     destination_env_name,
                                                                                     release_directory))

    release_directory = args[0]
    if object_type == 'table' and connection_name_arg is not None:
        connection_name = connection_name_arg.replace(" ", "_")
        release_full_directory = "{}/{}/{}/{}/".format(releases_root_directory, args[0],
                                                object_type_directory_map[plain_name_object_type_map[object_type]],
                                                       connection_name)
    else:
        release_full_directory = "{}/{}/{}/".format(releases_root_directory, args[0],
                                                object_type_directory_map[plain_name_object_type_map[object_type]])
    print("Importing named {} to environment destination: {} ".format(release_directory, destination_env_name))

    updates_to_guid_map = import_objects_from_release_directory(release_dir=release_full_directory)
    print("New parent:child guid map from import: {}".format(updates_to_guid_map))

    # Update the mapping file
    for p_guid in updates_to_guid_map:
        parent_child_guid_map[destination_env_name][p_guid] = updates_to_guid_map[p_guid]

    print("Writing new parent:child guid map")
    with open(parent_child_guid_map_json_file, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(parent_child_guid_map, indent=2))

    print("Finished with import")


if __name__ == "__main__":
   main(sys.argv[1:])