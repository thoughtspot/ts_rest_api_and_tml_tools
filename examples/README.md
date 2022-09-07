# Examples using ts_rest_api_and_tml_tools

The example scripts within this directory show practical use cases of the various aspects of the library. 

## main directory

For REST API-only use cases, please see https://github.com/thoughtspot/thoughtspot_rest_api_v1_python/tree/main/examples 

Any examples in this directory still use the wrapper Thoughtspot class, which will eventually be deprecated. The examples under thoughtspot_rest_api_v1_python use the REST API commands directly.

## tml_and_sdlc directory
The tml_and_sdlc sub-directory contains examples specific to manipulating ThoughtSpot Markup Language (TML) files and incorporating them into SDLC tools such as Git.

Every object in ThoughtSpot can be retrieved as a TML file in YAML format (or JSON as well when using the REST API). 

### tml_download.py
A basic framework for downloading all the objects of each type on ThoughtSpot to disk as YAML 

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

## localize
The localize sub-directory uses direct text token manipulation to change values within TML files, producing versions in new languages based on an original template.
