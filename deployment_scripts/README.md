# SDLC process command-line scripts
These scripts are all meant to be run from the command-line. They all use the shared 'thoughspot_release_config.toml' file to store information about the ThoughtSpot environment, local directories, etc.

Passwords are stored (encoded but not truly secure) on first use of the 'download_tml.py' script or using the '-p' option with any of the scripts.

You must publish the object types in the following order, as subsequent object types may reference objects from the previously published types:

1. table
2. view
3. worksheet
4. answer + liveboard

## thoughtspot_release_config.toml
Shared configuration file for all the command line scripts. Edit to include the details about the ThoughtSpot environment. Do not enter the password by editing the file directly - leave as "" or whatever it is encoded as, then use the '--password_reset' flag on any of the scripts to reset.

"parent_child_guid_map_file" needs to be a full filename to a .json file that will store the relationships between GUIDs in the various environments. This file will be created if it does not already exist.

The [thoughtspot_instances."dev"] / [thoughtspot_instances."prod"] section allows you to define connection details for any number of named ThoughtSpot instances. The key should match the {env_name} used elsewhere. The '-e' command-line argument of the scripts determines which is used 

The "[table_properties_map."{env_name}"]" section allows you to define any number of connection and database properties from the 'dev' environment that will get swapped with the value when creating the release files for Tables for that environment name.

You can specify match and replace in the *table_properties_map* at any level of specificity in the following order, using a dot to separate each level:

{ThoughtSpot Connection Name}.{db_name}.{schema}.{db_table_name}

If you only want to replace on Connection Name, your section would look like:

    [table_properties_map."prod"]
    "Original Connection 1" = "Destination Connection 1"
    "Bryant Snowflake" = "Bryant Snowflake PROD"

To match and replace on Connection Name, Database and Schema (notice the dot separating each 'level'):

    [table_properties_map."test"]
    "Bryant Snowflake.NEWRETAIL.RETAIL" = "Bryant Snowflake Test.RETAIL.PUBLIC"
    "Bryant Snowflake.SALES.PUBLIC" = "Bryant Snowflake Test.SALES.PUBLIC"
    "Bryant Snowflake.DATA_CHALLENGE.PUBLIC" = "Bryant Snowflake Test.DATA_CHALLENGE.PUBLIC"

The "level of specification" must match between all keys and values within one environmental configuration - the script will verify and exit if you accidentally have different levels between keys and values.

The [object_prefix_changes.{env_name}] section allows you to specify a transformation of a prefix from one environment to the next, if you have chosen that naming pattern. 

For example, if your dev environment objects all have names starting with "dev_", you can swap to another prefix with:

    [object_prefix_changes.test]
    previous_env_prefix = "dev_"
    new_env_prefix = "test_"

Or remove the prefix by setting new_env_prefix = "":
    
    [object_prefix_changes.prod]
    previous_env_prefix = "dev_"
    new_env_prefix = ""

If you want no transformation, leave both values set to ""
    [object_prefix_changes.prod]
    previous_env_prefix = ""
    new_env_prefix = ""


"sharing_groups_read_only", "sharing_groups_edit" are future features that have not been implemented yet.

## download_tml.py - Step 1
A command line script for downloading TML files. It uses the naming pattern of {guid}.{object_type}.tml and saves each object type to a directory.

Defaults to only downloading objects YOU own, with the '--all_objects' option available to admins to download everything.

Usage (all options have short forms like -p or -a): 

download_tml.py [--password_reset] [--config_file <alt_config.toml>] [--no_guids] [-e <environment_name>] [--all_objects] [-o <object_type>] 



Where object_type can be one of: all, liveboard, answer, table, worksheet, view

Example:

download_tml.py --all_objects -o worksheet

which would get ALL worksheet objects (if you are signed in to an admin account, vs. the default 'MY' option)

Environment Name defaults to 'dev', but you can specify an alternative using the '-e' argument. Ex.:

download_tml.py -e prod -o worksheet

## create_release_files.py - Step 2
Copies files downloaded using 'download_tml.py' into a 'release' directory, making any changes to connection details or object references (GUIDs/fqn property) so that the objects will publish to the "destination environment".

Usage (all options have short forms like -p or -a): 

create_release_files.py [--password_reset] [--config_file <alt_config.toml>] -o <object_type> -e <environment_name> <release_name>

Where object_type can be: liveboard, answer, table, worksheet, view")

Example:

create_release_files.py -o worksheet -e prod release_3

which copies everything stored in the 'worksheet' directory, replacing any GUID references with the mapping for the 'prod' environment, and places the new files into the '/{releases_directory}/release_3/worksheet/' directory

Table objects are split into sub-directories based on shared Connection Name (a "_" is substituted for any spaces). This allows the 'import_release_files.py' script to import all tables from the same Connection at the same time, which helps ThoughtSpot parse new objects as related, while limiting the overall size of the import.

## import_release_files.py - Step 3
Command line script to import the release built by 'create_release_files.py' to a ThoughtSpot instance

Usage (all options have short forms like -p or -a): 

import_release_files.py [--password_reset] [--config_file <alt_config.toml>] [-d <connection_name_subdirectory>] -o <object_type> -e <environment-name> <release-name>

Example:

import_release_files.py -o worksheet -e prod release_3

The '-d' / '--connection_name_subdirectory' option allows for specifying a single Connection Name to upload Tables from, since they are separated into sub-directories by 'import_release_files.py'.

## tml_details_from_directory.py
Best practices for storing TML on disk involve naming the file as {GUID}.{type}.tml, which does not give a user any information about what each file is without opening.

This script is designed to run from the command line and take either a directory or a file as an argument. 

Displays a pipe-delimited list of the TML files and the content name within the files.

# Other examples
Please see the /examples/tml_and_sdlc/ directory for additional examples of achieving workflows using TML + REST API together.