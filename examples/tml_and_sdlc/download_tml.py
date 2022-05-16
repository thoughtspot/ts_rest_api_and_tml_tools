import os
import requests.exceptions
import sys, getopt
from typing import List

from thoughtspot_rest_api_v1 import TSRestApiV1, MetadataNames, MetadataSubtypes
from thoughtspot_tml import *

config_file = 'thoughtspot_release_config.toml'

# I use a .env file locally to keep credentials out of the scripts themselves.
# You may want something more secure to protect admin credentials
from dotenv import load_dotenv
import toml

load_dotenv()

#
# STEP 1 SDLC Process
# download_tml.py is a command-line script to download sets of TML objects from a ThoughtSpot instance
# The purpose is to save to a source-control (Git or other) enabled directory with consistent file naming pattern
# Naming pattern is {Git root directory}/{object_type}/{GUID}.{object_type}.tml
# Existing files on disk will be overwritten completely, so you must Commit after runs to track the changes
#

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')  # or type in yourself, no trailing slash: 'https://{}.thoughtspotdev.cloud'
# This is the root directory, and then we have sub-directories for Pinboards, Answers, etc.
# for organizational purposes
# Needs to be fully qualified with trailing slash. MacOs example: /Users/{username}/Documents/thoughtspot_tml/
git_root_directory = os.getenv('git_directory')  # or type in yourself

# TML export does not include all GUIDs in the file, but they can be retrieved and added at download time
# Turn this flag OFF if you do not want the GUIDs to be added in (performance would be improved
add_guids_to_tml = True

def load_config():
    with open(config_file, 'r', encoding='utf-8') as cfh:
        parsed_toml = toml.loads(cfh.read())


# Eventually add tag-based search
#def get_tag_id_from_name(tag_name: str) -> List[str]:
#    tag_response = ts.metadata_list(object_type=MetadataNames.TAG, filter=tag_name)
#   for tag in tag_response['headers']:
#        if tag['name'] == tag_name:
#            return [tag['id']]
#    return None


# This will overwrite existing files downloaded before, which is intentional to
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

    # Create and login to REST APU
    ts: TSRestApiV1 = TSRestApiV1(server_url=server)
    try:
        ts.session_login(username=username, password=password)
    except requests.exceptions.HTTPError as e:
        print("Unable to sign-in with REST API session with following errors:")
        print(e)
        print(e.response.content)
        print("Exiting script...")
        exit()

    try:
        # metadata/list command retrieves list of headers, including the GUID
        objs = ts.metadata_list(object_type=object_type, sort='MODIFIED', sort_ascending=False,
                                category=category_filter, fetchids=object_guid_list, auto_created=False)

        #
        # You might add additional processing on the 'objs' results, for example looking at modified time or other properties,
        # to get to your final_objs List
        #

        final_objs = objs

        # Export one object at a time as YAML, for ease of parsing and saving
        # The REST APIs do allow requesting more than one TML object at a time, but you would need to separate
        # them out in the response and parse the GUIDs from there
        for obj in final_objs['headers']:
            guid = obj['id']
            try:
                if add_guids_to_tml is False:
                    tml_string = ts.metadata_tml_export_string(guid=guid, formattype='YAML')
                else:
                    # Request the TML along with the mapping of Data Object Names to GUI
                    if object_type in [MetadataNames.LIVEBOARD, MetadataNames.ANSWER, MetadataNames.WORKSHEET]:
                        tml_str, name_guid_map = ts.metadata_tml_export_string_with_associations_map(guid=guid)

                        tml_obj = YAMLTML.get_tml_object(tml_str)
                        tml_obj.add_fqns_from_name_guid_map(name_guid_map=name_guid_map)

                        tml_string = YAMLTML.dump_tml_object(tml_obj)
                    else:
                        tml_string = ts.metadata_tml_export_string(guid=guid, formattype='YAML')

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
            with open("{}/{}/{}.{}.tml".format(root_directory, object_type_directory_map[object_type], guid,
                                               object_type_directory_map[object_type]), 'w', encoding='utf-8') as f:
                f.write(tml_string)
    except requests.exceptions.HTTPError as e:
        print("Unable to request list of objects with following errors:")
        print(e)
        print(e.response.content)
        print("Exiting script...")
        exit()


def download_all_object_types(root_directory):
    object_types_to_download = [MetadataNames.LIVEBOARD,
                                MetadataNames.ANSWER,
                                MetadataSubtypes.TABLE,
                                MetadataSubtypes.WORKSHEET,
                                MetadataSubtypes.VIEW
                                ]
    for obj_type in object_types_to_download:
        download_objects_to_directory(root_directory=root_directory, object_type=obj_type)


def main(argv):
    print("Starting download of TML objects")
    try:
        opts, args = getopt.getopt(argv, "hat:o:nc:", ["all", "object_type=", "no_guids", "config_file="])
    except getopt.GetoptError:
        print('download_tml.py [--all] [-o <object_type>] [--no_guids] [--config_file <alt_config.toml>]')
        print("object_type can be: liveboard, answer, table, worksheet, view")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('download_tml.py -all -o <object_type> -i <inputfile> -o <outputfile>')
            print("object_type can be: liveboard, answer, table, worksheet, view")
            sys.exit()
        elif opt in ("-o", "--object_type"):
            print("Downloading all {}".format(arg))
            download_objects_to_directory(root_directory=git_root_directory, object_type=arg.lower(),
                                          category_filter='MY')
        elif opt in ("-a", "--all"):
            print("Downloading all objects of all object types")
            download_all_object_types(root_directory=git_root_directory)
        # The download script adds in all related objects with GUIDs, but this skips that you just want a pure archive
        # Should perform more quickly but makes SDLC process more difficult
        elif opt in ("-n", "--no_guids"):
            global add_guids_to_tml
            add_guids_to_tml = False
        elif opt in ("-c", "--config_file"):
            global config_file
            config_file = arg
            load_config()

    # Example of using function to download Liveboards
    download_objects_to_directory(root_directory=git_root_directory, object_type=MetadataNames.LIVEBOARD,
                                  category_filter='MY')
    print("Finished download")


if __name__ == "__main__":
    main(sys.argv[1:])