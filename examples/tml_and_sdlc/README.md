# Examples using ts_rest_api_and_tml_tools

The example scripts within this directory show practical use cases of the various aspects of the library. 

The tml_and_sdlc sub-directory contains examples specific to manipulating ThoughtSpot Markup Language (TML) files and incorporating them into SDLC tools such as Git.

Every object in ThoughtSpot can be retrieved as a TML file in YAML format (or JSON as well when using the REST API). 

## SDLC process command-line scripts
Please look at the /deployment_scripts directory for a set of command-line tools to do SDLC dev->test->prod releases using TML/

## tml_yaml_intro.py 
Short script showing the use of the YAMLTML object to parse YAML strings into TML objects, useful when reading/writing TML to disk

## tml_import_export_example.py
Basic examples of using the REST API library to retrieve TML from ThoughtSpot, convert to TML library objects, manipulate then import back to ThoughtSpot.

## tml_change_references_example.py
Basic example showing the methods for adjusting the object references for each object type. Useful as a simple reference (along with the main README), vs. a more complete process like tml_replicate_from_existing_on_server.py.  

## tml_from_scratch.py
Table and Worksheet objects can be built programmatically from a base template, then published and shared.

This script shows the functions for starting a new TML and adding columns referenced correctly. 

A Worksheet can be generated from a single input Table. More complex Worksheets with joins should be built as a template in ThoughtSpot, then modified as needed.

## transfer_object_ownership.py
Best practice workflows for using Git with ThoughtSpot use object ownership to keep some content locked to a given user for edits. 

This script has functions for finding the necessary metadata to transfer the ownership of any objects, and could be the foundation of a running web service for this purpose. 

## merge_tml_change.sh
BASH script to keep the GUID from one TML file while replacing with the body of another file


