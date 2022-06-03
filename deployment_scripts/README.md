# SDLC process command-line scripts
This repository hosts a suite of command-line tools implementing the development and deployment best practices from https://developers.thoughtspot.com/docs/?pageid=development-and-deployment. 

These scripts are all meant to be run from the command-line. Give them executable permissions and they should run without issue (will need to be run with './' in front of the filename unless you put the directory in your PATH).

They all use the shared 'thoughspot_release_config.toml' file to store information about the ThoughtSpot environment, local directories, etc.

Credentials are stored (encoded but not truly secure) on first use of the 'download_tml.py' script or using the '-p' option (always resets credentials) with 'download_tml.py' or 'import_release_files.py.

You must publish the object types in the following order, as subsequent object types may reference objects from the previously published types:

1. table
2. view
3. worksheet
4. answer + liveboard

The scripts are built after a development pattern where content from "dev" (the first stage, actively developed on) is transformed and pushed to any other stage. This is to say, moving from "dev" to "test" starts with the TML files from "dev", but so does moving from "test" to "prod" - the "dev" files are transformed into their prod form, rather than using the "test" stage files and modifying for prod. Each 'stage' uses the "dev" parent files, as all changes must originate in 'dev'.

An example of using the scripts to deploy from "dev" to "test". First you would configure 'thoughtspot_release_config.toml' with details of your 'dev' and 'test' environments, then on command line run the commands in the following order:

    download_tml.py --all_objects -o all

    create_release_files.py -o table -e test -r test_release_1
    import_release_files.py -o table -e test -r test_release_1

    create_release_files.py -o view -e test -r test_release_1
    import_release_files.py -o view -e test -r test_release_1

    create_release_files.py -o worksheet -e test -r test_release_1
    import_release_files.py -o worksheet -e test -r test_release_1

    create_release_files.py -o answer -e test -r test_release_1
    import_release_files.py -o answer -e test -r test_release_1

    create_release_files.py -o liveboard -e test -r test_release_1
    import_release_files.py -o liveboard -e test -r test_release_1
    
## Getting Started
You'll need to have currently supported version of Python 3 installed (3.7+). 

1. Download all the files in this GitHub sub-directory to your machine (they do not use any of the other files in the wider repository). 

2. Install the latest versions of the 'thoughtspot_tml' and 'thoughtspot_rest_api-v1' modules from pip


    pip install thoughtspot-rest-api-v1 --upgrade
    pip install thoughtspot-tml --upgrade

3. Create a directory on disk for the 'dev' TML files to be placed in by the 'download_tml.py' script. You will specify this directory with the 'git_directory' property in the 'thoughtspot_release_config.toml' file.

4. Create a directory on disk to be the root directory the 'release' TML files to written to. You will specify this directory with the 'releases_directory' property in the 'thoughtspot_release_config.toml' file.

5. Decide where you want the parent:child GUID map JSON file to be created (the scripts will create and maintain this file, you just decide on a location). You will specify this directory with the 'parent_child_guid_map_file' property in the 'thoughtspot_release_config.toml' file.

For version control, enable Git or your preferred source control system on the directories that you've created. The 'git_directory' is the most important one to enable version control on, as it contains TML from the 'dev' environment. Release files can be considered temporary and may be generated new for any number of reasons.

## thoughtspot_release_config.toml
The 'thoughtspot_release_config.toml' is the shared configuration file for all the command line scripts. It configures overall file system details and environment details for 'dev' ThoughtSpot instance. 

"parent_child_guid_map_file" needs to be a full filename to a .json file that will store the relationships between GUIDs in the various environments. This file will be created if it does not already exist.

The [environment_config_files] section defines additional configuration files for each environment. The 'key' allows a short identifier to be passed in the command line arguments using the '-e' argument. 

    [environment_config_files]
    test = "test_config.toml"
    prod = "prod_config.toml"

When you run a command like:

    create_release_files.py -o table -e test -r test_release_1

The '-e' argument will look to the 'environment_config_files' section of 'thoughtspot_release_config.toml' first, then look for any other files with the naming pattern of '{env_name}_config.toml', so you do not need to list every config file you have here if they follow that pattern - this is useful when you have a number of multi-tenant environments to deploy to.

Within the individual destination environment config files ("test_config.toml", "prod_config.toml" etc.), you can configure the ThoughtSpot instance details (server, username, etc). as well as the following:

### Table Object Transformations - Connection, Database, etc.
The "[table_properties_map] section of an enviornment config file allows you to define any number of connection and database properties from the 'dev' environment that will get swapped with the value when creating the release files for Tables for that environment name.

You can specify match and replace in the *table_properties_map* at any level of specificity in the following order, using a dot to separate each level:

{ThoughtSpot Connection Name}.{db_name}.{schema}.{db_table_name}

If you only want to replace on Connection Name, your section would look like:

    [table_properties_map]
    "Original Connection 1" = "Destination Connection 1"
    "Bryant Snowflake" = "Bryant Snowflake PROD"

To match and replace on Connection Name, Database and Schema (notice the dot separating each 'level'):

    [table_properties_map]
    "Bryant Snowflake.NEWRETAIL.RETAIL" = "Bryant Snowflake Test.RETAIL.PUBLIC"
    "Bryant Snowflake.SALES.PUBLIC" = "Bryant Snowflake Test.SALES.PUBLIC"
    "Bryant Snowflake.DATA_CHALLENGE.PUBLIC" = "Bryant Snowflake Test.DATA_CHALLENGE.PUBLIC"

The "level of specification" must match between all keys and values within one environmental configuration - the script will verify and exit if you accidentally have different levels between keys and values.

### Changing Object Names when using Prefixes
The [object_prefix_changes] section of an environment config file allows you to specify a transformation of a prefix from one environment to the next, if you have chosen that naming pattern. 

For example, if your dev environment objects all have names starting with "dev_", you can swap to another prefix with:

    [object_prefix_changes]
    previous_env_prefix = "dev_"
    new_env_prefix = "test_"

Or remove the prefix by setting new_env_prefix = "":
    
    [object_prefix_changes]
    previous_env_prefix = "dev_"
    new_env_prefix = ""

If you want no transformation, leave both values set to ""
    
    [object_prefix_changes]
    previous_env_prefix = ""
    new_env_prefix = ""

### Sharing Groups config
The 'import_release_files.py' script can set the imported objects to be shared to groups with the 
"sharing_groups_read_only" and "sharing_groups_edit" sections. Use the group name (not the group display name) to specify which groups you want each object type shared to and whether they should have read-only or edit access:

    [sharing_groups_read_only]
    table = ['group_1', 'test_viewers']
    view = []
    worksheet = []
    answer = ['test_viewers']
    liveboard = ['test_viewers']
    
    [sharing_groups_edit]
    table = ['data_devs', 'semi_admins']
    view = []
    worksheet = []
    answer = []
    liveboard = []

## download_tml.py - Step 1
A command line script for downloading TML files. It uses the naming pattern of {guid}.{object_type}.tml and saves each object type to a directory.

Defaults to only downloading objects YOU own, with the '--all_objects' option available to admins to download everything.

Usage (all options have short forms like -p or -a): 

    download_tml.py [--password_reset] [--config_file <alt_config.toml>] [--no_guids] [-e <environment_name>] [--all_objects] [-o <object_type>] 

Where object_type can be one of: all, liveboard, answer, table, worksheet, view

Example:

    download_tml.py --all_objects -o worksheet

which would get ALL worksheet objects (if you are signed in to an admin account, vs. the default 'MY' option)

Environment Name defaults to use the 'thoughtspot_release_config.toml', but you can specify an alternative using the '-e' argument. Ex.:

    download_tml.py -e prod -o worksheet

## create_release_files.py - Step 2
Copies files downloaded using 'download_tml.py' into a 'release' directory, making any changes to connection details or object references (GUIDs/fqn property) so that the objects will publish to the "destination environment".

Usage (all options have short forms like -c or -a): 

    create_release_files.py [--config_file <alt_config.toml>] -o <object_type> -e <environment_name> -r <release_name>

Where object_type can be: liveboard, answer, table, worksheet, view")

You cannot reset the password from 'create_release_files.py' since it does not use the REST API at all.

Example:

    create_release_files.py -o worksheet -e prod -r release_3

which copies everything stored in the 'worksheet' directory, replacing any GUID references with the mapping for the 'prod' environment, and places the new files into the '/{releases_directory}/release_3/worksheet/' directory

Table objects are split into sub-directories based on shared Connection Name (a "_" is substituted for any spaces). This allows the 'import_release_files.py' script to import all tables from the same Connection at the same time, which helps ThoughtSpot parse new objects as related, while limiting the overall size of the import.

## import_release_files.py - Step 3
Command line script to import the release built by 'create_release_files.py' to a ThoughtSpot instance

Usage (all options have short forms like -p or -a): 

    import_release_files.py [--password_reset] [--config_file <alt_config.toml>] [-d <connection_name_subdirectory>] -o <object_type> -e <environment-name> -r <release-name>

Example:

    import_release_files.py -o worksheet -e prod -r release_3

The '-d' / '--connection_name_subdirectory' option allows for specifying a single Connection Name to upload Tables from, since they are separated into sub-directories by 'import_release_files.py'.

## tml_details_from_directory.py
Best practices for storing TML on disk involve naming the file as {GUID}.{type}.tml, which does not give a user any information about what each file is without opening.

This script is designed to run from the command line and take either a directory or a file as an argument. 

Displays a pipe-delimited list of the TML files and the content name within the files.

# Other examples
Please see the /examples/tml_and_sdlc/ directory for additional examples of achieving workflows using TML + REST API together.
