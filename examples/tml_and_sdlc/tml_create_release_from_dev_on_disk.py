import os
from collections import OrderedDict
from thoughtspot import *
from tml import *

#
# This example follows best practices to create a new "release" from an existing set of TML files
# The original TML files from the 'dev' environment are replicated on disk, then modified with any
# transformations necessary for the new 'environment' they will be published to
# GUIDs from the new 'environment' are substituted
#

# This assumes that you have named your files on pattern {GUID}.{objectType}.tml or just {GUID}.tml
# We keep the original dev GUID as the filename, regardless of which environment we publish to
# This allows using the GUID mapping file when publishing, even after the GUID has been changed in the YAML of the file

directory_structure_map = OrderedDict({
    "tables" : "tables",
    "worksheets": "worksheets",
    "answers" : "answers",
    "liveboards" : "liveboards"
})

# Source of the template files. Should be structured as /tables , /worksheets , /answers , /liveboards
template_files_directory_root = ''

# Where the output the files prior to publish
new_build_destination_directory = ''

# Mapping file of dev GUIDs to any previously published objects in prod
mapping_file = 'mapping.json'
with open(mapping_file) as fh:
    full_mapping = json.loads(fh.read())
mapping_env_name = 'prod'  # This might be 'prod', 'test', or an organization ID in a multi-tenant publish
dev_to_env_map = full_mapping[mapping_env_name] # Just get the map for this env
# map looks like:
# { 'envName' : { 'dev_guid' : 'env_guid', ... } }
#
#


for dir in directory_structure_map:
    # First generate all the files to be published in the destination directory

    # Read each file in the dev directory
    dev_directory = "{}/{}".format(template_files_directory_root, dir)
    dest_directory = "{}/{}".format(new_build_destination_directory, dir)
    dir_list = os.listdir(dev_directory)

    # Two Lists, each with the files to either be updated (create_new=False) or make new (create_new=True)
    update_files = []
    new_files = []
    # Here we write the files to /new and /update sub-directories in the 'build' under each objectType
    # This allows for deploying everything in the directory from a separate script without
    # having to re-determine what type of action to take
    for filename in dir_list:
        # Ignore files that don't end in .tml
        if filename.find('.tml') != -1:
            with open(dev_directory + "/" + filename, 'r') as fh:
                yaml_str = fh.read()
            tml_obj = TML(YAMLTML.load_string(yaml_str))
            # Determine if file has been published before to server using mapping file
            if tml_obj.guid in dev_to_env_map:
                # Substitute the guid from the new environment
                tml_obj.guid = dev_to_env_map[tml_obj.guid]
                update_files.append(filename)
                # Write the modified file with the same filename to new build directory
                with open(dest_directory + "/update/" + filename, 'w') as fh:
                    fh.write(YAMLTML.dump_tml_object(tml_obj))
            else:
                new_files.append(filename)
                tml_obj.remove_guid()  # Ensures a new object is created
                # Write the modified file with the same filename to new build directory
                with open(dest_directory + "/new/" + filename, 'w') as fh:
                    fh.write(YAMLTML.dump_tml_object(tml_obj))

    # Separate into another script?
    # Now publish the files and get any new GUIDs

    # New files first
    new_tml_list = []  # We'll load all the TMLs at once especially for tables, it helps with JOINs
    new_tml_orig_guid_list = []  # Store the GUIDs in order for recording to the mapping after publish
    for filename in new_files:
        with open(dest_directory + "/new/" + filename, 'r') as fh:
            yaml_str = fh.read()
        tml_obj = TML(YAMLTML.load_string(yaml_str))
        # Use the GUID from the filename, which should be the original GUID from dev environment
        # The 'new' TML files should have no GUID in the YAML at this point
        # Filename will have . separator, the first item will be the GUID itself
        new_tml_orig_guid_list.append(filename.split('.')[0])
        new_tml_list.append(tml_obj)

    #
    # Sign in to ThoughtSpot REST API
    #
    username = os.getenv('username')  # or type in yourself
    password = os.getenv('password')  # or type in yourself
    server = os.getenv('server')  # or type in yourself

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

    # Run validation
    validation_response = ts.tsrest.metadata_tml_import(tml=new_tml_list, create_new_on_server=True, validate_only=True)
    # If validation passes (what does this look like), run the import
    try:
        import_response = ts.tsrest.metadata_tml_import(tml=new_tml_list, create_new_on_server=True)
        response_details = ts.tsrest.raise_tml_errors(import_response)
        new_tml_import_guid_list = ts.tsrest.guids_from_imported_tml(import_response)
        # Run through the two lists (should be the same length) and then add to mapping
        if len(new_tml_import_guid_list) != len(new_tml_orig_guid_list):
            raise Exception("The length of the imported files does not match the original list")
        i = 0
        for o_guid in new_tml_import_guid_list:
            # Map o_guid = new_guid
            full_mapping[mapping_env_name][o_guid] = new_tml_import_guid_list[i]
            i += 1

        with open(mapping_file, 'r') as fh1:
            # Create a copy of the previous mapping before update
            # Replace with os copy?
            with open(mapping_file + ".old", 'w') as fh2:
                fh2.write(fh1.read())
        # Update the main mapping file with the newly updated JSON structure with the new GUIDs
        with open(mapping_file, 'w') as fh:
            fh.write(json.dumps(full_mapping))

    except SyntaxError as e:
        print(e)
        # Choose how you want to recover from here if there are issues (possibly not exit whole script)
        exit()

    # Publish the updates (no new GUIDs)
    new_tml_list = []  # We'll load all the TMLs at once especially for tables, it helps with JOINs
    for filename in update_files:
        with open(dest_directory + "/update/" + filename, 'r') as fh:
            yaml_str = fh.read()
        tml_obj = TML(YAMLTML.load_string(yaml_str))
        # Use the GUID from the filename, which should be the original GUID from dev environment
        # The 'new' TML files should have no GUID in the YAML at this point
        # Filename will have . separator, the first item will be the GUID itself
        new_tml_list.append(tml_obj)
    # Run validation
    validation_response = ts.tsrest.metadata_tml_import(tml=new_tml_list, create_new_on_server=False, validate_only=True)
    # If validation passes (what does this look like), run the import
    try:
        import_response = ts.tsrest.metadata_tml_import(tml=new_tml_list, create_new_on_server=False)
        response_details = ts.tsrest.raise_tml_errors(import_response)
    except SyntaxError as e:
        print(e)
        # Choose how you want to recover from here if there are issues (possibly not exit whole script)
        exit()







