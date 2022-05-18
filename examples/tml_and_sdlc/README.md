# Examples using ts_rest_api_and_tml_tools

The example scripts within this directory show practical use cases of the various aspects of the library. 

The tml_and_sdlc sub-directory contains examples specific to manipulating ThoughtSpot Markup Language (TML) files and incorporating them into SDLC tools such as Git.

Every object in ThoughtSpot can be retrieved as a TML file in YAML format (or JSON as well when using the REST API). 

## SDLC process command-line scripts
These scripts are all meant to be run from the command-line. They all use the shared 'thoughspot_release_config.toml' file to store information about the ThoughtSpot environment, local directories, etc.

Passwords are stored (encoded but not truly secure) on first use of the 'download_tml.py' script or using the '-p' option with any of the scripts.

You must publish the object types in the following order, as subsequent object types may reference objects from the previously published types:

1. table
2. view
3. worksheet
4. answer + liveboard

### thoughtspot_release_config.toml
Shared configuration file for all the command line scripts. Edit to include the details about the ThoughtSpot environment. Do not enter the password by editing the file directly - leave as "" or whatever it is encoded as, then use the '--password_reset' flag on any of the scripts to reset.

The "[connection_name_map]" section allows you to define any number of Connection Names from the 'dev' environment that will get swapped with the value when creating the release files for Tables. 

"parent_child_guid_map_file" needs to be a full filename to a .json file that will store the relationships between GUIDs in the various environments. This file will be created if it does not already exist.

### download_tml.py - Step 1
A command line script for downloading TML files. It uses the naming pattern of {guid}.{object_type}.tml and saves each object type to a directory.

Defaults to only downloading objects YOU own, with the '--all_objects' option available to admins to download everything.

Usage (all options have short forms like -p or -a): 

download_tml.py [--password_reset] [--config_file <alt_config.toml>] [--no_guids] [--all_objects] [-o <object_type>] 



Where object_type can be one of: all, liveboard, answer, table, worksheet, view

Example:

download_tml.py --all_objects -o worksheet

which would get ALL worksheet objects (if you are signed in to an admin account, vs. the default 'MY' option)

### create_release_files.py - Step 2
Copies files downloaded using 'download_tml.py' into a 'release' directory, making any changes to connection details or object references (GUIDs/fqn property) so that the objects will publish to the "destination environment".

Usage (all options have short forms like -p or -a): 

create_release_files.py [--password_reset] -o <object_type> -e <environment_name> <release_name>

Where object_type can be: liveboard, answer, table, worksheet, view")

Example:

create_release_files.py -o worksheet -e prod release_3

which copies everything stored in the 'worksheet' directory, replacing any GUID references with the mapping for the 'prod' environment, and places the new files into the '/{releases_directory}/release_3/worksheet/' directory

Table objects are split into sub-directories based on shared Connection Name (a "_" is substituted for any spaces). This allows the 'import_release_files.py' script to import all tables from the same Connection at the same time, which helps ThoughtSpot parse new objects as related, while limiting the overall size of the import.

### import_release_files.py - Step 3
Command line script to import the release built by 'create_release_files.py' to a ThoughtSpot instance

Usage (all options have short forms like -p or -a): 

import_release_files.py [--password_reset] [-c <connection name>] -o <object_type> -e <environment-name> <release-name>

Example:

import_release_files.py -o worksheet -e prod release_3

## Other examples

### tml_yaml_intro.py 
Short script showing the use of the YAMLTML object to parse YAML strings into TML objects, useful when reading/writing TML to disk

### tml_import_export_example.py
Basic examples of using the REST API library to retrieve TML from ThoughtSpot, convert to TML library objects, manipulate then import back to ThoughtSpot.

### tml_change_references_example.py
Basic example showing the methods for adjusting the object references for each object type. Useful as a simple reference (along with the main README), vs. a more complete process like tml_replicate_from_existing_on_server.py.  

### tml_from_scratch.py
Table and Worksheet objects can be built programmatically from a base template, then published and shared.

This script shows the functions for starting a new TML and adding columns referenced correctly. 

A Worksheet can be generated from a single input Table. More complex Worksheets with joins should be built as a template in ThoughtSpot, then modified as needed.

### tml_replicate_from_existing_on_server.py
Large script which replicates all targeted objects on a ThoughtSpot instance, modifying the TML references as necessary to generate an identical 'environment'.

Will be updated in the near future to take advantage of recent functionality and best-practices

### tml_create_release_from_dev_on_disk.py
Eventual example (coming soon) for creating a new 'release' from saved 'dev' environment on disk. 

Shows how to build from files stored in Git directories per best practice

### transfer_object_ownership.py
Best practice workflows for using Git with ThoughtSpot use object ownership to keep some content locked to a given user for edits. 

This script has functions for finding the necessary metadata to transfer the ownership of any objects, and could be the foundation of a running web service for this purpose. 

### tml_details_from_directory.py
Best practices for storing TML on disk involve naming the file as {GUID}.{type}.tml, which does not give a user any information about what each file is without opening.

This script is designed to run from the command line and take either a directory or a file as an argument. 

Displays a pipe-delimited list of the TML files and the content name within the files.

### merge_tml_change.sh
BASH script to keep the GUID from one TML file while replacing with the body of another file


