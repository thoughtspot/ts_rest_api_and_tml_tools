#!/usr/bin/env python3

import os
import requests.exceptions
import sys, getopt
from typing import List
import getpass
import base64

from thoughtspot_rest_api_v1 import TSRestApiV1, MetadataNames, MetadataSubtypes
from thoughtspot_tml import *

# TOML config file for sharing settings between deployment scripts
# You may want something more secure to protect admin level credentials, particularly password
import toml
config_file = 'thoughtspot_release_config.toml'

#
# STEP 1 SDLC Process
# download_tml.py is a command-line script to download sets of TML objects from a ThoughtSpot instance
# The purpose is to save to a source-control (Git or other) enabled directory with consistent file naming pattern
# Naming pattern is {Git root directory}/{object_type}/{GUID}.{object_type}.tml
# Existing files on disk will be overwritten completely, so you must Commit after runs to track the changes
#

#
# GLOBAL VARIABLES
#
token_expiration_days = 30  # How long to request token if using in days
username = ""
cred = ""
server = ""
cred_type = ""

# This is the root directory, and then we have sub-directories for Pinboards, Answers, etc.
# for organizational purposes
# Needs to be fully qualified with trailing slash. MacOs example: /Users/{username}/Documents/thoughtspot_tml/
git_root_directory = ""

# TML export does not include all GUIDs in the file, but they can be retrieved and added at download time
# Turn this flag OFF if you do not want the GUIDs to be added in (performance would be improved)
add_guids_to_tml = True

#
# END GLOBAL VARIABLES
#


# All of the scripts share a TOML config file. This function sets all the global vars based on the config
# new_password=True triggers the password reset flow which stores the password encoded (not encrypted!)
def load_config(environment_name, new_password=False):
    save_password = None
    with open(config_file, 'r', encoding='utf-8') as cfh:
        global server
        global git_root_directory
        global username
        global cred
        global cred_type
        main_config_toml = toml.loads(cfh.read())
        use_second_config = False

        # A few properties are shared across all from main config
        git_root_directory = main_config_toml['git_directory']

        # Use the main config file is no environment_name declared
        if environment_name == "" or environment_name is None:
            print('Using main config')
            server = main_config_toml['server']
            username = main_config_toml['username']
            # password = main_config_toml['p_do_not_enter_manually']
            cred = main_config_toml['cred_set_automatically']
            cred_type = main_config_toml['cred_type']
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


# Eventually add tag-based search
#def get_tag_id_from_name(tag_name: str) -> List[str]:
#    tag_response = ts.metadata_list(object_type=MetadataNames.TAG, filter=tag_name)
#   for tag in tag_response['headers']:
#        if tag['name'] == tag_name:
#            return [tag['id']]
#    return None


#
# Main function to bring down the TML objects and save them to disk.
# Will overwrite existing files downloaded before, which is intentional.
#
def download_objects_to_directory(root_directory, object_type,
                                  object_guid_list=None, category_filter=None):
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
        'liveboard': MetadataNames.LIVEBOARD,
        'answer': MetadataNames.ANSWER,
        'table': MetadataSubtypes.TABLE,
        'worksheet': MetadataSubtypes.WORKSHEET,
        'view': MetadataSubtypes.VIEW
    }

    # All input of the 'plain names' from the command line
    if object_type in plain_name_object_type_map.keys():
        object_type = plain_name_object_type_map[object_type]

    # Create and login to REST API using the global variables set by the load_config() function
    ts: TSRestApiV1 = TSRestApiV1(server_url=server)
    try:
        if cred_type == 't':
            ts.session_login_v2(token=cred)
        elif cred_type == 'p':
            ts.session_login(username=username, password=cred)
    except requests.exceptions.HTTPError as e:
        print("Unable to sign-in with REST API session with following errors:")
        print(e)
        print(e.response.content)
        print("Exiting script...")
        exit()

    try:
        # metadata/list command retrieves list of headers, including the GUID
        # You could build out other filtering possibilities (tags for example) as needed
        objs = ts.metadata_list(object_type=object_type, sort='MODIFIED', sort_ascending=False,
                                category=category_filter, fetchids=object_guid_list, auto_created=False)

        #
        # You might add additional processing on the 'objs' results, for example looking at modified time
        # or other properties, to get to your final_objs List
        #
        final_objs = objs

        # Export one object at a time as YAML, for ease of parsing and saving
        # The REST APIs do allow requesting more than one TML object at a time, but you would need to separate
        # them out in the response and parse the GUIDs from there
        for obj in final_objs['headers']:
            guid = obj['id']
            try:
                # The global "add_guids_to_tml" flag skips the process of adding the GUIDs to the FQN property
                # It directly outputs the string as received from the API
                # Useful to use as a comparison to the standard process, which parses the results using thoughtspot_tml
                if add_guids_to_tml is False:
                    tml_string = ts.metadata_tml_export_string(guid=guid, formattype='YAML')
                # Request the TML along with the mapping of Data Object Names to GUID
                else:
                    # Table objects do not have any additional GUIDs to add (at this time)
                    if object_type in [MetadataSubtypes.TABLE]:
                        tml_string = ts.metadata_tml_export_string(guid=guid, formattype='YAML')
                    else:
                        tml_str, name_guid_map = ts.metadata_tml_export_string_with_associations_map(guid=guid)

                        tml_obj = YAMLTML.get_tml_object(tml_str)
                        tml_obj.add_fqns_from_name_guid_map(name_guid_map=name_guid_map)

                        tml_string = YAMLTML.dump_tml_object(tml_obj)

            # Some TML errors come back in the JSON response of a 200 HTTP, but a SyntaxError will be thrown
            except SyntaxError as e:
                e_msg = str(e)
                # There are some objects that the metadata list calls return when user is an admin
                # but are system objects that can't be exported. This ignores those errors and keeps moving
                # without even printing the error
                if e_msg.find('lack of access') == -1:
                    print('TML export encountered error:')
                    print(e)
                continue

            # Naming pattern is {Git root}/{object_type}/{GUID}.{object_type}.tml
            object_dir = "{}/{}/".format(root_directory, object_type_directory_map[object_type])
            # Create the object path if it does not yet exist
            if os.path.exists(object_dir) is False:
                print("Creating the path to: {}".format(object_dir))
                os.makedirs(object_dir)
            with open("{}/{}/{}.{}.tml".format(root_directory, object_type_directory_map[object_type], guid,
                                               object_type_directory_map[object_type]), 'w', encoding='utf-8') as f:
                f.write(tml_string)
    except requests.exceptions.HTTPError as e:
        print("Unable to request list of objects with following errors:")
        print(e)
        print(e.response.content)
        print("Exiting script...")
        exit()


#
# Function to run through all of the object types
#
def download_all_object_types(root_directory, category_filter):
    object_types_to_download = [MetadataSubtypes.TABLE,
                                MetadataSubtypes.VIEW,
                                MetadataSubtypes.WORKSHEET,
                                MetadataNames.ANSWER,
                                MetadataNames.LIVEBOARD
                                ]
    for obj_type in object_types_to_download:
        download_objects_to_directory(root_directory=root_directory, object_type=obj_type,
                                      category_filter=category_filter)


#
# Command-line argument parsing for the script
#
def main(argv):
    print("Starting download of TML objects")
    password_reset = False
    category_filter = 'MY'   # default only download YOUR content, override with all
    env_name = ''  # Main config is assumed to be 'dev' environment
    try:
        opts, args = getopt.getopt(argv, "hae:o:nc:p", ["all_objects", "object_type=", "no_guids", "config_file=", "password_reset"])
    except getopt.GetoptError:
        print('download_tml.py [--password_reset] [--config_file <alt_config.toml>] [--no_guids] [--all_objects] [-o <object_type>]   ')
        print("object_type can be: all, liveboard, answer, table, worksheet, view")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('download_tml.py [--password_reset] [--config_file <alt_config.toml>] [--no_guids] [--all] [-o <object_type>]   ')
            print("object_type can be: all, liveboard, answer, table, worksheet, view")
            sys.exit()
        # '-e' is the the environment-name
        # In general, download is most useful from the 'dev' environment, but you may want to archive from any of them
        elif opt in ("-e"):
            env_name = arg
        elif opt in ("-p", "--password_reset"):
            password_reset = True
        # The download script adds in all related objects with GUIDs, but this skips that you just want a pure archive
        # Should perform more quickly but makes SDLC process more difficult
        elif opt in ("-n", "--no_guids"):
            global add_guids_to_tml
            add_guids_to_tml = False
        # Allows using an alternative TOML config file from the default
        elif opt in ("-c", "--config_file"):
            global config_file
            config_file = arg
        # Shift the list request from "MY" to "ALL", useful as an admin
        elif opt in ("-a", "--all_objects"):
            category_filter = 'ALL'
        # What object type should be downloaded, including 'all' option
        elif opt in ("-o", "--object_type"):
            load_config(environment_name=env_name, new_password=password_reset)
            object_type = arg.lower()
            if object_type not in ["all", "liveboard", "answer", "table", "worksheet", "view"]:
                print("-o / --object_type can be one of: all, liveboard, answer, table, worksheet, view")
                print("Exiting...")
                exit()
            if object_type in ['all', 'any']:
                print("Downloading {} objects of all object types".format(category_filter.lower()))
                download_all_object_types(root_directory=git_root_directory, category_filter=category_filter)
            else:
                print("Downloading {} objects of {} type".format(category_filter.lower(), arg))
                download_objects_to_directory(root_directory=git_root_directory, object_type=arg.lower(),
                                              category_filter=category_filter)
    print("Finished download")


if __name__ == "__main__":
    main(sys.argv[1:])