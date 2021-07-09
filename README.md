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
    users = ts.user.list()
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

### Shared Methods
Because many of the metadata operations use the same base API method, with options that are specific to the object type, there is a `SharedEndpointMethods` class which defines some basic shared actions.

    SharedEndpointMethods.list()
    SharedEndpointMethods.find_guid()
    SharedEndpointMethods.get_object_by_id()
    SharedEndpointMethods.details()
    SharedEndpointMethods.assign_tags()

You will actually use these through an endpoint, but they are all defined identically up in the SharedEndpointMethods class:

    users = ts.user.list()
    groups = ts.group.list()


## TML Workflows
### Finding the IDs to export/download a TML file
If you want to work with an object that already exists on a ThoughtSpot Server, you'll need to find its ID/GUID. 

If you go to the Developer Portal in TS Cloud, you can use the menus to manually find the GUID of any object.

The REST API also allows retrieving lists of different object types, which you can go through to identify the ones you want (or do things to all of them).

For example, if you want to change the Answers on a Pinboard from one Worksheet to another, you would do:

1. Use the REST API to get the GUID of the Pinboard 
2. Request the TML via the REST API
3. Create a Pinboard object to give model to work with the TML


        # Find the Pinboard
        pb_guid = ts.pinboard.find_guid('Pinboard Name to Change')
        pb_tml = ts.tml.export_tml(guid=pb_guid)

        # Create a Pinboard TML object
        pb = Pinboard(pb_tml)

### Changing References (Switching a Pinboard to a different Worksheet, Worksheet to different tables etc.)
One of the primary use cases of TML is taking an existing object (a Pinboard for example) and either making a copy that maps to a different Worksheet, or just updating the original. 

There are object references within the TML, that need GUIDs from the Server. Using the REST API commands, you can get these GUIDs.

This extends our example from above, pulling the guid of a Worksheet and replacing it within the TML object.

    # Find the GUID of the Worksheet to switch to
    new_worksheet_name = 'Worksheet We are Switching To'
    ws_guid = ts.worksheet.find_guid(new_worksheet_name)
  
    # You need to specify the original Worksheet name, in case not all Answers use
    # that particular WS. It will only replace where it finds a match
    o_pb_ws_name = 'Original WS'

    # Switch Pinboard to the new worksheet
    pb.update_worksheet_on_all_answers_by_fqn(original_worksheet_name=o_pb_ws_name, new_worksheet_guid_for_fqn=wg_guid)
    
    # Import (upload) to Update (create_new_on_server=False)
    # The GUID of the TML object will be used so the Server knows what to update
    ts.tml.import_tml(tml=pb.tml, create_new_on_server=False)  # Set to True to create a new Pinboard


### Opening a TML file from disk
If you are downloading TML, you are probably storing it as YAML (the native format). When using the REST API and the TML objects of this library, everything defaults to the JSON format.

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
A Pinboard is a combination of Answers, but each Answer lives fully within the TML of the Pinboard (that is to say, Answers on a Pinboard live in the Pinboard object fully, they are not links to Answer objects stored independently in ThoughtSpot).

The TML for an Answer within a Pinboard is almost identical to the TML for separately stored Answer. The Pinboard class has a special `.answers_as_objects` property that returns a list of Answer objects automatically.

    pb_obj = Pinboard(ts.export_tml(guid=pb_guid))
    answers = pb_obj.answers_as_objects  # Returns list of Answer objects from Pinboard
    for a in answers:
        print(a.search_query)


### Answer class
An Answer is a Saved Search, and is loaded with the Search bar and other editing features visible. It is a single table or visualization with many options.

As mentioned above in the Pinboard class, the TML for an independent Answer is identical to an Answer within a Pinboard, so the same object type is used for both.

    answer_obj = Answer(ts.export_tml(guid=answer_guid))
    print(answer_obj.search_query)
    answer_obj.set_table_mode()
    answer_obj.description = 'This is a great answer'



### Table class

