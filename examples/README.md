# Examples using ts_rest_api_and_tml_tools

The example scripts within this directory show practical use cases of the various aspects of the library. 

## main directory


## tml_and_sdlc
The tml_and_sdlc sub-directory contains examples specific to manipulating ThoughtSpot Markup Language (TML) files and incorporating them into SDLC tools such as Git.

Every object in ThoughtSpot can be retrieved as a TML file in YAML format (or JSON as well when using the REST API). 

### tml_download.py
A basic framework for downloading all the objects of each type on ThoughtSpot to disk as YAML 

### tml_yaml_intro.py
Short script showing the use of the YAMLTML object to parse YAML strings into TML objects, useful when reading/writing TML to disk

 - *transfer_object_ownership.py* : Best practice workflows for using Git with ThoughtSpot use object ownership to keep some content locked to a given user for edits. This script has functions for finding the necessary metadata to transfer the ownership of any objects, and could be the foundation of a running web service for this purpose. 
 - *merge_tml_change.sh* : BASH script to keep the GUID from one TML file while replacing with the body of another file
 - 

## localize
The localize sub-directory uses direct text token manipulation to change values within TML files, producing versions in new languages based on an original template.
