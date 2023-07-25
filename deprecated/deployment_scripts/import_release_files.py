#!/usr/bin/env python3

import os
import json
import requests.exceptions
import sys, getopt
from typing import List, Dict
import getpass
import base64

from thoughtspot_rest_api_v1 import TSRestApiV1, TSTypes, ShareModes

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
env_name = ''  # Main config is assumed to be 'dev' environment, will be overridden by command line argument
token_expiration_days = 30  # How long to request token if using in days
username = ""
cred = ""
server = ""
cred_type = ""
# This is the root directory, and then we have sub-directories for Pinboards, Answers, etc.
# for organizational purposes
# Needs to be fully qualified with trailing slash. MacOs example: /Users/{username}/Documents/thoughtspot_tml/
orig_git_root_directory = ""
releases_root_directory = ""

parent_child_guid_map = {}
parent_child_guid_map_json_file = ""

# Sharing to certain groups after import creates the "environment" on the ThoughtSpot instance
sharing_groups_read_only = {}
sharing_groups_edit = {}

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
        global username
        global cred
        global cred_type
        global parent_child_guid_map
        global sharing_groups_read_only
        global sharing_groups_edit

        main_config_toml = toml.loads(cfh.read())
        use_second_config = False

        # A few properties are shared across all from main config
        orig_git_root_directory = main_config_toml['git_directory']
        releases_root_directory = main_config_toml['releases_directory']

        # Use the main config file is no environment_name declared
        if environment_name == "" or environment_name is None:
            print('Using main config')
            server = main_config_toml['server']
            username = main_config_toml['username']
            # password = main_config_toml['p_do_not_enter_manually']
            cred = main_config_toml['cred_set_automatically']
            cred_type = main_config_toml['cred_type']
            sharing_groups_read_only = main_config_toml['sharing_groups_read_only']
            sharing_groups_edit = main_config_toml['sharing_groups_edit']

        else:
            use_second_config = True
            # Look at the 'environment_config_files' in the main config file
            if environment_name in main_config_toml['environment_config_files']:
                second_config_file = main_config_toml['environment_config_files'][environment_name]
                # Try looking for a file with format "{env_name}_config.toml"
                if os.path.exists(second_config_file) is False:
                    second_config_file = main_config_toml['environment_config_files'][environment_name] + "_config.toml"
                    if os.path.exists(second_config_file) is False:
                        print("Cannot find defined configuration for environment_name '{}' in {} or '{}_config.toml".format(environment_name, config_file, environment_name))
                        print("Exiting...")
                        exit()
                with open(second_config_file, 'r', encoding='utf-8') as cfh2:
                    second_config_toml = toml.loads(cfh2.read())

                    server = second_config_toml['server']
                    username = second_config_toml['username']
                    cred = second_config_toml['cred_set_automatically']
                    cred_type = second_config_toml['cred_type']
                    sharing_groups_read_only = main_config_toml['sharing_groups_read_only']
                    sharing_groups_edit = main_config_toml['sharing_groups_edit']

        #
        # Replace with other secure form of password retrieval if needed, this is basic encoded for convenience
        #
        if cred == "" or new_password is True:
            password = getpass.getpass("Please enter ThoughtSpot password on {} for configured username {}: ".format(server, username))
            # Ask about saving password
            while save_password is None:
                save_password_input = input("Save credential to config file? Y/n: ")
                if save_password_input.lower() == 'y':
                    save_password = True
                    # Write encoded to TOML file at end
                elif save_password_input.lower() == 'n':
                    save_password = False
        else:
            e_cred = cred
            d_cred = base64.standard_b64decode(e_cred)
            cred = d_cred.decode(encoding='utf-8')
    if save_password is True:

        # Request token with expiration per global (in seconds)
        token_expiry_seconds = token_expiration_days * 24 * 60 * 60
        # Create and login to REST API using the global variables set by the load_config() function
        # Try to use the V2 login if available first
        if cred_type == 't':
            ts: TSRestApiV1 = TSRestApiV1(server_url=server)
            try:
                ts.session_login_v2(username=username, password=password)
                t_resp = ts.get_token_v2(username=username, password=password, token_expiry_duration=token_expiry_seconds)
                cred = t_resp['token']
            except requests.exceptions.HTTPError as e:
                # Try the V1 login if V2 doesn't exist, switch to p credential
                cred_type = 'p'
                cred = password

        print("Saving credentials encoded to config file...")
        bytes_pw = cred.encode(encoding='utf-8')
        e_pw = base64.standard_b64encode(bytes_pw)
        if use_second_config is False:
            main_config_toml['cred_set_automatically'] = str(e_pw, encoding='ascii')
            main_config_toml['cred_type'] = cred_type
            with open(config_file, 'w', encoding='utf-8') as cfh:
                cfh.write(toml.dumps(main_config_toml))
        else:
            second_config_toml['cred_set_automatically'] = str(e_pw, encoding='ascii')
            second_config_toml['cred_type'] = cred_type
            with open(second_config_file, 'w', encoding='utf-8') as cfh2:
                cfh2.write(toml.dumps(second_config_toml))

    # Parent:Child GUID map loading
    # To be able to update objects in another environment, we store a mapping of the "child guid" created from the
    # publishing of an object from the 'dev' environment, which becomes the 'parent guid'
    # This creates the JSON file for the mappings if it does not exist already
    parent_child_guid_map_json_file = main_config_toml['parent_child_guid_map_file']
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
    TSTypes.LIVEBOARD: 'liveboard',
    TSTypes.ANSWER: 'answer',
    TSTypes.TABLE: 'table',
    TSTypes.WORKSHEET: 'worksheet',
    TSTypes.VIEW: 'view'
}

# Mapping of the metadata object types to the directory to save them to
plain_name_object_type_map = {
    'liveboard': TSTypes.LIVEBOARD,
    'answer':  TSTypes.ANSWER,
    'table': TSTypes.TABLE,
    'worksheet': TSTypes.WORKSHEET,
    'view': TSTypes.VIEW
}


#
# Function that parses through the release directories of TML files and imports them using Import TML
# Tables are imported together by sub-directory (which are split by Connection Name in 'create_release_files.py' )
#
def import_objects_from_release_directory(release_dir, object_type):
    # Create and login to REST API using the global variables set by the load_config() function
    ts: TSRestApiV1 = TSRestApiV1(server_url=server)
    try:
        if cred_type == 't':
            ts.session_login_v2(token=cred)
        elif cred_type == 'p':
            ts.session_login(username=username, password=cred)
    except requests.exceptions.HTTPError as e:
        print("There was an issue with the saved credentials, please re-enter password to try again")
        load_config(environment_name=env_name, new_password=True)
        try:
            if cred_type == 't':
                ts.session_login_v2(token=cred)
            elif cred_type == 'p':
                ts.session_login(username=username, password=cred)
        except requests.exceptions.HTTPError as e:
            print(
                "Unable to sign-in with REST API session with following errors, please check the config file and run again with -p to reset credentials")
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
        guids_from_import = []
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
            #with open('../examples/tml_and_sdlc/import_error.log', 'w', encoding='utf-8') as efh:
            #    efh.write(e.response.request.body)
            print("Exiting after failure...")
            exit()
        # TML Import can return a 200 with a JSON response indicating the status of TML parsing, which can have Errors
        # This raises a SyntaxError, which can then be parsed as such:
        except SyntaxError as e:
            print('TML import encountered error:')
            print(e)
            #with open('../examples/tml_and_sdlc/import_error.log', 'w', encoding='utf-8') as efh:
            #    efh.write(str(e))
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

        # Share to groups if any sharing defined
        # Skip if no sharing group names are defined. Reminder this is the groupName not the displayName
        if len(sharing_groups_read_only[object_type]) > 0 or len(sharing_groups_edit[object_type] > 0):
            print("Sharing imported objects with configured Groups")
            # Get all group details to retrieve the GUIDs
            read_only_guids = []
            edit_guids = []
            for group_name in sharing_groups_read_only[object_type]:
                group_resp = ts.group_get(name=group_name)
                guid = group_resp['header']['id']  # double check this
                read_only_guids.append(guid)

            for group_name in sharing_groups_edit[object_type]:
                group_resp = ts.group_get(name=group_name)
                guid = group_resp['header']['id']  # double check this
                edit_guids.append(guid)

            permissions = ts.get_sharing_permissions_dict()
            for g in read_only_guids:
                ts.add_permission_to_dict(permissions_dict=permissions, guid=g,
                                          share_mode=ShareModes.READ_ONLY)
            for g in edit_guids:
                ts.add_permission_to_dict(permissions_dict=permissions, guid=g, share_mode=ShareModes.EDIT)
            try:
                ts.security_share(shared_object_type=plain_name_object_type_map[object_type],
                                  shared_object_guids=guids_from_import, permissions=permissions, notify_users=False)
            except requests.exceptions.HTTPError as e:
                print(e)
                print(e.response.content)
                print(e.response.request.url)
                print("Exiting after REST API failure...")
                exit()
#
# Command-line argument parsing for the script
#
def main(argv):
    global destination_env_name
    new_password = False
    object_type = None
    connection_name_arg = None
    release_directory = None
    try:
        opts, args = getopt.getopt(argv, "hpc:d:o:e:", ["password_reset", "object_type="])
    except getopt.GetoptError:

        print("import_release_files.py [--password_reset] [--config_file <alt_config.toml>] [-d <connection name_subdirectory>] -o <object_type> -e <environment-name> -r <release-name>")
        print("object_type can be: liveboard, answer, table, worksheet, view")
        print("Will create directories if they do not exist")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("import_release_files.py [--password_reset] [-d <connection name_subdirectory>] -o <object_type> -e <environment-name> -r <release-name>")
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
        elif opt in ('-r', '--release_name'):
            release_directory = arg

    load_config(environment_name=destination_env_name, new_password=new_password)
    # parent_child_guid_map_env = parent_child_guid_map[destination_env_name]

    if release_directory is None:
        print("Please use '-r' or '--release_name' option to specify a release name")
        print("Exiting...")
        exit()
    if object_type not in ["liveboard", "answer", "table", "worksheet", "view"]:
        print("Must include -o or --object_type argument with value: liveboard, answer, table, worksheet, view")
        print("Exiting...")
        exit()
    print("Creating release files for {} type to environment {} with name {}".format(object_type,
                                                                                     destination_env_name,
                                                                                     release_directory))

    if object_type == 'table' and connection_name_arg is not None:
        connection_name = connection_name_arg.replace(" ", "_")
        release_full_directory = "{}/{}/{}/{}/".format(releases_root_directory, release_directory,
                                                object_type_directory_map[plain_name_object_type_map[object_type]],
                                                       connection_name)
    else:
        release_full_directory = "{}/{}/{}/".format(releases_root_directory, release_directory,
                                                object_type_directory_map[plain_name_object_type_map[object_type]])
    print("Importing named {} to environment destination: {} ".format(release_directory, destination_env_name))

    updates_to_guid_map = import_objects_from_release_directory(release_dir=release_full_directory,
                                                                object_type=object_type)
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