# tml_tools
Simple library for programmatic importing, exporting and changing TML documents

## Components
tsrest.py provides the TSRest class, which implements the Public ThoughtSpot REST API. 

tml.py provides a TML base class, along with descendant classes for particular object types: Table, Worksheet, Answer, Pinboard etc.

## Importing the classes
    from tsrest import TSRest
    from tml import *

## Logging into the REST API
You create the TSRest object with the `server` argument, then use the `login()` method with username and password to log in. After login succeeds, the TSRest object has an open requests.Session object which maintains the necessary cookies to use the REST API continuously .


    username = os.getenv('username')  # or type in yourself
    password = os.getenv('password')  # or type in yourself
    server = os.getenv('server')      # or type in yourself

    ts: TSRest = TSRest(server=server)
    try:
        ts.login(username=username, password=password)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)

## Finding the IDs to export/download a TML file
If you want to work with an object that already exists on a ThoughtSpot Server, you'll need to find its ID/GUID. 

If you go to the Developer Portal in TS Cloud, you can use the menus to manually find the GUID of any object.

The REST API also allows retrieving lists of different object types, which you can go through to identify the ones you want (or do things to all of them).



## Opening a TML file from disk

## Creating a TML object from what the REST API retrieves
TML files are in YAML format, which easily transforms into JSON. The REST API allows you to request as either YAML or JSON. 

Because Python has a native 'json' package which easily converts JSON into a Python Dict, the tml_tools library by default downloads in JSON format and returns a Python Dict.

You can then work with the Python Dict representing the TML.

The `TSRest.export_tml(guid=)` method will download and do this conversion for you.

Then there are the TML classes (Table, Pinboard, etc.) which take the resulting Dict and give easy access to the structure, including defined properties with setter and getter capabilities.

    table_obj = Table(ts.export_tml(guid=first_table_id))
    print(table_obj.db_table)
    table_obj.db_table = "new_table_name"

## Importing/Publishing TML back to ThoughtSpot Server
The import_tml() method lets you push the TML Dict back to the Server
    
    TSRest.import_tml(tml, create_new_on_server=False, validate_only=False, formattype='JSON'))

There are a few optional arguments: 
- `create_new_on_server` - you must set this to True, otherwise it will update the existing object with the same GUID.
- `validate_only` - If set to True, this only runs through validation and returns back the response with any errors listed
- `formattype` - No use for end users currently, but could allow for YAML string upload directly, for manually edited TML files on disk.

## TML Objects
You can create a base TML object, which only has the .content and .content_name properties

    tml_obj = TML(tml)
    tml_obj.content["additional_keys"]["sub-keys"]

But if you know the type of object, then you can use one of the descendant objects to give
more built in properties to access rather than having to work through the .content property.

### Pinboard class

### Table class