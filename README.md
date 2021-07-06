# ts_rest_api_and_tml_tools
Repository contains:
- A simple implementation of the ThoughtSpot REST API (tsrestapiv1), based entirely on the public documentation
- The 'ThoughtSpot' class for using the REST API to accomplish common tasks
- TML classes for working with files in the ThoughtSpot Modeling Language (TML)

It is developed by ThoughtSpot CS and SE team members and is not supported by ThoughtSpot support.

## Components
- thoughtspot.py provides a class for doing actions to the ThoughtSpot Server, organized with a series of sub-objects which represent the various object types in ThoughtSpot
    - endpoint_method_classes.py is implements the individual classes which are objects under the ThoughtSpot class    
- tsrestapiv1.py provides the TSRestApiV1 class, which implements the Public ThoughtSpot REST API available under /public/v1/ .
    - Uses the requests Python library for all HTTP activity
- tml.py provides a TML base class, along with descendant classes for particular object types: Table, Worksheet, Answer, Pinboard etc.

## Importing the classes
    from thoughtspot import *
    from tml import *

You don't need to import tsrestv1.py, it is available as the `.tsrest` object from ThoughtSpot    

## Logging into the REST API
You create the ThoughtSpot object with the `server` argument, then use the `login()` method with username and password to log in. After login succeeds, the TSRest object has an open requests.Session object which maintains the necessary cookies to use the REST API continuously .


    username = os.getenv('username')  # or type in yourself
    password = os.getenv('password')  # or type in yourself
    server = os.getenv('server')      # or type in yourself

    ts: ThoughtSpot = ThoughtSpot(server=server)
    try:
        ts.login(username=username, password=password)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)

## Logging out of the REST API
The `logout()` method of the ThoughtSpot class will send the API request to end your TS session. After you do this, you may want to del the ThoughtSpot object if you are doing a lot of other work to end the request.Session object:
    
    ts.logout()
    del ts

## REST API Workflows
### Sub-objects of ThoughtSpot class
When you instantiate an object from the ThoughtSpot class, sub-objects are created of each of the classes in endpoint_method_classes.py ,as well as a TSRestApiV1 object.

The allows you to access methods for the ThoughtSpot object types using an organized syntax, which works well with autocomplete in IDEs:
    
    ts: ThoughtSpot = ThoughtSpot(server=server)
    try:
        ts.login(username=username, password=password)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)
    users = ts.user.list_users()
    privs = ts.group.privileges_for_group()
    pdf = ts.pinboard.pdf_export()

#### "direct" REST API calls
There is a  `.tsrest` object available under `ThoughtSpot` which is the instantiated TSRestApiV1 object that all the other classes use to make the REST API calls. The `login()` and `logout()` methods of `ThoughtSpot` class actually make a call to this internal TSRestApiV1 object.

If you are testing / confirming how the REST API calls work, or want to use options that are not represented by the Endpoint Method Classes, you can directly use `ThoughtSpot.tsrest` to get to all the methods of the TSRestApiV1 class.

### ENUM data structures
The ThoughtSpot API has internal namings for many features, which require looking up in the reference guide. To help out, the tsrestapiv1.py file defines several ENUM style classes:

- MetadataNames: The namings used in the 'type' parameter of the /metadata/ endpoint calls, with simplified names that matches the names in the UI and standard ThoughtSpot documentation. For example, MetadataNames.GROUP = 'USER_GROUP'
- ShareModes: The modes used in the JSON of the /security/share endpoint
- Privileges: The name of the Privileges that Groups can have (and users can inherit) in ThoughtSpot

### 


## TML Workflows
### Finding the IDs to export/download a TML file
If you want to work with an object that already exists on a ThoughtSpot Server, you'll need to find its ID/GUID. 

If you go to the Developer Portal in TS Cloud, you can use the menus to manually find the GUID of any object.

The REST API also allows retrieving lists of different object types, which you can go through to identify the ones you want (or do things to all of them).

For example, if you want to change the Answers on a Pinboard from one Worksheet to another, you would do the following:

    pb_guid = ts.pinboard.find_guid('Pinboard Name to Change')
    pb_tml = ts.tml.export_tml(guid=pb_guid)
    ws_guid = ts.worksheet.find_guid(



### Opening a TML file from disk

### Creating a TML object from what the REST API retrieves
TML files are in YAML format, which easily transforms into JSON. The REST API allows you to request as either YAML or JSON. 

Because Python has a native 'json' package which easily converts JSON into a Python Dict, the tml_tools library by default downloads in JSON format and returns a Python Dict.

You can then work with the Python Dict representing the TML.

All TML REST API actions are accessed under `ThoughtSpot.tml`, which is an object of the TMLMethods class from endpoint_method_classes.py.

The `ThoughtSpot.tml.export_tml(guid=)` method will download and do this conversion for you.

Then there are the TML classes (Table, Pinboard, etc.), defined in tml.py which take the resulting Dict and give easy access to the structure, including defined properties with setter and getter capabilities.

    table_obj = Table(ts.export_tml(guid=first_table_id))
    print(table_obj.db_table)
    table_obj.db_table = "new_table_name"

## Importing/Publishing TML back to ThoughtSpot Server
The import_tml() method lets you push the TML Dict back to the Server
    
    ThoughtSpot.tml.import_tml(tml, create_new_on_server=False, validate_only=False, formattype='JSON'))

There are a few optional arguments: 
- `create_new_on_server` - you must set this to True, otherwise it will update the existing object with the same GUID.
- `validate_only` - If set to True, this only runs through validation and returns the response with any errors listed
- `formattype` - No use for end users currently, but could allow for YAML string upload directly, for manually edited TML files on disk.

## TML Objects
You can create a base TML object, which only has the .content and .content_name properties

    tml_obj = TML(tml)
    tml_obj.content["additional_keys"]["sub-keys"]

But if you know the type of object, then you can use one of the descendant objects to give
more built in properties to access rather than having to work through the .content property.

### Pinboard class

### Table class
