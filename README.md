# ts_rest_api_and_tml_tools
ts_rest_api_and_tml_tools is a simple Python implementation of the ThoughtSpot V1 REST API and a library for working with ThoughtSpot Modeling Language (TML) files.

Repository contains:
- A simple implementation of the ThoughtSpot REST API (tsrestapiv1), based entirely on the public documentation
- The 'ThoughtSpot' class for using the REST API to accomplish common tasks
- TML classes for working with files in the ThoughtSpot Modeling Language (TML)

It is developed by ThoughtSpot CS and SE team members and is not supported by ThoughtSpot support.

You can use tsrestapiv1.py as a cross-reference with the Swagger portal on your ThoughtSpot instance and the reference documentation (https://developers.thoughtspot.com/docs/?pageid=rest-api-reference) to implement any V1 REST API command correctly.

The V2 ThoughtSpot REST API is currently in preview. All requests in V2 will be in JSON format, with a complete Playground environment, and there will be SDKs automatically provided in various languages to issue the endpoint commands.

ts_rest_api_and_tml_tools is developed and tested only against ThoughtSpot Cloud using the available tspublic/v1 endpoints. 

It should also work with Software versions 7.1.1 and later, but the library is not versioned, so please check your documentation for available endpoints within the release you use if on a Software release.

All code and examples are intended only as a starting point to be customized to your purposes. Nothing is wrapped up and documented for "production" out of the box.

For a library of tools which includes support for older Software versions of ThoughtSpot and built out command-line utilities, please see https://github.com/thoughtspot/cs_tools . 

## Contents
 - Getting Started
 - REST API (thoughtspot.py)
 - TML (tml.py) 


## Getting Started
### Components
- thoughtspot.py provides a class for doing actions to the ThoughtSpot Server, organized with a series of sub-objects which represent the various object types in ThoughtSpot
    - endpoint_method_classes.py is implements the individual classes which are objects under the ThoughtSpot class    
- tsrestapiv1.py provides the TSRestApiV1 class, which implements the Public ThoughtSpot REST API available under /public/v1/ .
    - Uses the requests Python library for all HTTP activity
- tml.py provides a TML base class, along with descendant classes for particular object types: Table, Worksheet, Answer, Liveboard etc.

### Importing the classes
    from thoughtspot import *
    from tml import *

You don't need to import tsrestv1.py, it is available as the `.tsrest` sub-object from the `ThoughtSpot` class.    

### Logging into the REST API
You create a ThoughtSpot object with the `server` argument, then use the `login()` method with username and password to log in. After login succeeds, the TSRest object has an open requests.Session object which maintains the necessary cookies to use the REST API continuously .


    username = os.getenv('username')  # or type in yourself
    password = os.getenv('password')  # or type in yourself
    server = os.getenv('server')      # or type in yourself

    ts: ThoughtSpot = ThoughtSpot(server=server)
    try:
        ts.login(username=username, password=password)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)

### Logging out of the REST API
The `logout()` method of the ThoughtSpot class will send the API request to end your TS session. After you do this, you may want to del the ThoughtSpot object if you are doing a lot of other work to end the request.Session object:
    
    ts.logout()
    del ts

## REST API (thoughtspot.py)
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
    pdf = ts.liveboard.pdf_export()

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

### Finding the IDs of objects in ThoughtSpot
If you want to work with an object that already exists on a ThoughtSpot Server, you'll need to find its ID/GUID. 

If you go to the Developer Portal in TS Cloud, you can use the menus to manually find the GUID of any object.

The REST API also allows retrieving lists of different object types, which you can go through to identify the ones you want (or do things to all of them).

For example, if you want to change the Answers on a Liveboard from one Worksheet to another, you would do:

        # Find the Liveboard
        lb_guid = ts.liveboard.find_guid('Liveboard Name to Change')


## TML (tml.py)
TML can be exported as YAML or JSON. When using a YAML workflow, the 'oyaml' library is used in place of the standard PyYAML library.

oyaml returns an OrderedDict structure, so that the order of YAML exported from ThoughtSpot is maintained when dumped back to string form.

### 

### Retrieving the TML as a Python OrderedDict from REST API
If you want to use the TML classes to programmatically adjust the returned TML, there is a `export_tml(guid)` method which retrieves the TML from the API in JSON format and then returns it as a Python OrderedDict.

This method is designed to be the input into all of the TML descendant classes

    lb_tml = ts.tml.export_tml(guid=lb_guid)
    # Create a Liveboard TML object
    lb_obj = Liveboard(lb_tml)
    # Or do it all in one step: 
    lb_obj = Liveboard(ts.tml.export_tml(guid=lb_guid))

### Opening a TML file from disk and loading into a TML class object
The YAMLTML object contains static methods to help with correct import and formatting of ThoughtSpot's TML YAML.

    fh = open('tml_file.worksheet.tml', 'r')
    tml_yaml_str = fh.read()
    fh.close()

    tml_yaml_ordereddict = YAMLTML.load_string_to_ordereddict(tml_yaml_str)

    tml_obj = Worksheet(tml_yaml_ordereddict)

    tml_obj.description = "Adding a wonderful description to this document"

    modified_tml_string = YAMLTML.dump_tml_object_to_yaml_string(tml_obj)
    fh = open('modified_tml.worksheet.tml', 'w')
    fh.write(modified_tml_string)

Full example of working with a YAML string in `examples/tml_and_sdlc/tml_yaml_intro.py`.

### Downloading the TML directly as string
If you want the TML as you would see it within the TML editor, use
`ThoughtSpot.tml.export_tml_string(guid, formattype)`

or

`ThoughtSpot.tsrest.metadata_tml_export_string(guid, formattype)`

formattype defaults to 'YAML' but can be set to 'JSON'.

This method returns a Python str object, which can then be editing in memory or saved directly to disk. 

Example of saving to disk is available in `examples/tml_and_sdlc/tml_download.py`.

### Creating a TML object from what the REST API retrieves
TML files are in YAML format, which easily transforms into JSON. The REST API allows you to request as either YAML or JSON. 

Because Python has a native 'json' package which easily converts JSON into a Python Dict, the tml_tools library by default downloads in JSON format and returns a Python Dict.

You can then work with the Python Dict representing the TML.

All TML REST API actions are accessed under `ThoughtSpot.tml`, which is an object of the TMLMethods class from endpoint_method_classes.py.

The `ThoughtSpot.tml.export_tml(guid=)` method will download and do this conversion for you.

Then there are the TML classes (Table, Liveboard, etc.), defined in tml.py which take the resulting Dict and give easy access to the structure, including defined properties with setter and getter capabilities.

    table_obj = Table(ts.export_tml(guid=first_table_id))
    print(table_obj.db_table)
    table_obj.db_table = "new_table_name"

### Importing/Publishing TML back to ThoughtSpot Server
The import_tml() method lets you push the TML Dict back to the Server

The TML Dict is stored as the `.tml` property of any TML class (Worksheet.tml, Answer.tml, etc.). You must reference the `.tml` property when sending into `.import_tml()`

    ThoughtSpot.tml.import_tml(tml, create_new_on_server=False, validate_only=False))

You can also import multiple TML files at the same time by sending a List of the tml dicts:
    
    ThoughtSpot.tml.import_tml([wb_obj_1.tml, wb_obj_2.tml], create_new_on_server=True)

There are a few optional arguments: 
- `create_new_on_server` - you must set this to True, otherwise it will update the existing object with the same GUID.
- `validate_only` - If set to True, this only runs through validation and returns the response with any errors listed'

There is a static method for pulling the GUIDs from the import command response `ts.tsrest.guids_from_imported_tml()`, which returns the GUIDs in a list in the order they were sent to the import.

Example:

    # Get create Worksheet object
    ws_obj = Worksheet(ts.tml.export_tml(guid=lb_guid))
    # Send the .tml property, not the whole object
    import_response = ts.tml.import_tml(ws_obj.tml, create_new_on_server=False)
    new_guids = ts.tsrest.guids_from_imported_tml(import_response)
    new_guid = new_guids[0]  # when only a single TML imported

NOTE: If you use 'create_new_on_server=True' but are uploading from a TML that has an existing GUID property, use the `.remove_guid()` method on the TML object first, to make sure any old references are cleared and the new object creates successfully.

## TML Objects
You can create a base TML object, which only has the .content and .content_name properties

    tml_obj = TML(tml)
    tml_obj.content["additional_keys"]["sub-keys"]

But if you know the type of object, then you can use one of the descendant objects to give
more built in properties to access rather than having to work through the .content property.

Remember: make sure you are referencing the property from `TML.content['{key_1}']['{key_2}]` when you are setting changes - if you have made and modified a variable from the original values, it may not be part of the `.content` dictionary unless you fully qualify.

### Table class
Table objects are the fundamental component of data models in ThoughtSpot, representing the actual table-like objects on a data source (tables, views, etc.)

Table objects also hold the Row Level Security rules in ThoughtSpot.

#### Modifying Connection details
Connections in ThoughtSpot all have unique names, so to switch a Table to a different connection, use the `Table.connection_name` property

    table_obj.connection_name = 'New Connection Name'

The `Table.change_connection_by_name(original_connection_name: str, new_connection_name: str)` method exists as well to safely change the name only if the original connection name matches the provided value. This allows for safe find/replace over a number of files / objects.

The other properties are available to modify as well:

 - db_name
 - schema
 - db_table

#### Table Columns
To access existing columns as a List, use the `Table.columns` property

To add a column, first use `Table.create_column()` to retrieve a column object, then use `Table.add_column()` to add the column to the end of the existing list. `Table.add_columns()` takes a List of columns to add many at once.

    new_column = table_obj.create_column(column_display_name='Pretty Name', db_column_name='db_name_of_col', column_data_type='INT64'
                      column_type='ATTRIBUTE', index_type='DONT_INDEX')
    table_obj.add_column(new_column)


See the reference guide https://docs.thoughtspot.com/cloud/latest/tml#syntax-tables for string values of these properties.


#### Creating a Table TML programmatically
The Table class has a static method called `generate_tml_from_scratch(connection_name: str, db_name: str, schema: str, db_table: str)` which returns a str in YAML format with the start of a Table TML and no columns.

The string template can then be loaded into a Table constructor using `YAMLTML.load_string_to_ordereddict()` to give a blank

    tml_yaml_str = Table.generate_tml_from_scratch(connection_name='Main Snowflake Connection', db_name="IMPORTANT_DATABASE,
                                                   schema='PUBLIC', db_table='MY_TABLE')
    tml_obj = Table(YAMLTML.load_string_to_ordereddict(tml_yaml_str)

A full example of creating a Table TML programmatically is available in examples/tml_and_sdlc/tml_from_scratch.py.


### Worksheet class
Worksheets are the data model layer presented to end users. They present a single controlled source from multiple tables with many additional controls on how columns are displayed and indexed.

#### Changing Table references in a Worksheet
Tables, unlike Connections, do not have fully unique names in ThoughtSpot. If there is more than one Table with the same name, you will need to use the GUID of the table to identify it. 

The property in TML for a GUID reference is `fqn:` . 

Worksheet class provides the `remap_tables_to_new_fqn(name_to_fqn_map: Dict)` method to perform a GUID swap. You create a Dict of { 'name' : 'fqn' } structure, then pass it in and the correct TML manipulations will happen calling the `change_table_by_fqn()` method.

    name_guid_map = { 'Table 1' : '0f814ce1-dba1-496a-b3de-38c4b9a288ed', 'Table 2' : '2e7a0676-2acf-4700-965c-efebf8c0b594'}
    ws_obj.remap_table_to_new_fqn(name_to_fqn_map=name_guid_map)

#### Creating a Worksheet programmatically from a Table TML
If you want to make a worksheet on top of a single table, you can generate the Worksheet programmatically from that Table TML

The Worksheet class has a static method called `generate_tml_from_scratch(worksheet_name: str, table_name: str)` which returns a str in YAML format with the start of a Worksheet TML and no columns.

The string template can then be loaded into a Worksheet constructor using `YAMLTML.load_string_to_ordereddict()` to give a blank

    tml_yaml_str = Worksheet.generate_tml_from_scratch(worksheet_name='Great Worksheet', table_name=table_tml_obj.content_name)
    tml_obj = Worksheet(YAMLTML.load_string_to_ordereddict(tml_yaml_str)

A full example of creating a Worksheet TML programmatically is available in examples/tml_and_sdlc/tml_from_scratch.py.

#### Worksheet Columns

### Liveboard class
A Liveboard is a combination of Answers, but each Answer lives fully within the TML of the Liveboard (that is to say, Answers on a Liveboard live in the Liveboard object fully, they are not links to Answer objects stored independently in ThoughtSpot).

The TML for an Answer within a Liveboard is almost identical to the TML for separately stored Answer. The Liveboard class has a special `.answers_as_objects` property that returns a list of Answer objects automatically.

    pb_obj = Liveboard(ts.export_tml(guid=pb_guid))
    answers = pb_obj.answers_as_objects  # Returns list of Answer objects from Liveboard
    for a in answers:
        print(a.search_query)

#### Changing the Order or Size of Answers
Liveboards have an `answers` section that defines each answer, and then a `layout` section that defines the order and sizing of the answers. 

The 'tiles' section of the Layout is an ordered list / array. The order the elements appear in the tiles list is the order they will appear in the Liveboard, then space optimized based on the sizes that have been chosen.

There is an enum `Liveboard.TileSizes` to use to get the strings for the layout sizes.

To change the order or sizing, access the `Liveboard.layout_tiles` property. Each element will have `visualization_id` and `size`:

    pb_obj = Liveboard(ts.export_tml(guid=pb_guid))
    tiles = pb_obj.layout_tiles  # This makes a copy, so you will have to reset pb_obj.layout_tiles = tiles later to save your changes to the object
    for tile in tiles:
        if tiles['size'] == pb_obj.TileSizes.MEDIUM:
            tile['size'] = pb_obj.TileSizes.LARGE
    # Adjust the order using regular Python List methods 
    tiles.reverse()  # Flips the order
    # You must set the Liveboard object property to the new version
    pb_obj.layout_tiles = tiles

#### Removing an Answer from a Liveboard
Removing an Answer requires removing the Answer section and the reference in the layout section. For this reason, the action has been encapsulated into a method:

`Liveboard.remove_answer_by_index(index: int)`

The index refers to the order of the Answer in the Answer section, rather than the visible order, which is determined in the layout section. You'll have to look at the TML of the Liveboard to determine the index necessary to do what you want (Answers can have the same name and definition so it's hard to identify them any other way than their order).

`Liveboard.remove_answer_by_layout_index(index: int)`

looks to the Layout section, finds the Answer at the given index in that section, then removes in both places.

#### Adding an Answer to a Liveboard
Because Answers use the same TML when stored separately or on a Liveboard, you can add an Answer object right into an existing Liveboard. You must specify the layout order and sizing (or it will default to the end and default size).

The `Liveboard.add_answer_by_index(answer: Answer, index: int, tile_size: str)` method performs all the necessary insertions. You pass an Answer object, the index for layout, and a size, and it adds the correct sections to the Liveboard TML.

In this example, we'll grab an existing Answer and add it to a Liveboard:

    a_id = ts.answer.find_guid(name='Answer 1')
    # Create the Answer object
    a_obj = Answer(tml_dict=ts.tml.export_tml(guid=a_id))
    
    pb_id = ts.liveboard.find_guid(name='My Liveboard')
    pb_obj = Liveboard(tml_dict=ts.tml.export_tml(guid=pb_id))
    #  Add the Answer    
    pb_obj.add_answer_by_index(answer=a_obj, index=4, tile_size=pb_obj.TileSizes.EXTRA_LARGE)
    
    # Publish
    # If you want to creat new, make sure to kill the existing GUID
    # pb_obj.remove_guid()
    response = ts.tml.import_tml(tml=pb_obj.tml, create_new_on_server=False, validate_only=False)
    print(response)

### Answer class
An Answer is a Saved Search, and is loaded with the Search bar and other editing features visible. It is a single table or visualization with many options.

As mentioned above in the Liveboard class, the TML for an independent Answer is identical to an Answer within a Liveboard, so the same object type is used for both.

    answer_obj = Answer(ts.export_tml(guid=answer_guid))
    print(answer_obj.search_query)
    answer_obj.set_table_mode()
    answer_obj.description = 'This is a great answer'

The Answer class has an ENUM of all the possible chart types:

`Answer.ChartTypes`

Whether the Answer displays as a Chart or a Table is the `display_mode` property, which is directly accessible but has also been wrapped with:

    Answer.set_chart_mode()
    Answer.set_table_mode()




### Changing References (Switching a Liveboard to a different Worksheet, Worksheet to different tables etc.)
One of the primary use cases of TML is taking an existing object (a Liveboard for example) and either making a copy that maps to a different Worksheet, or just updating the original. 

There are object references within the TML, that need GUIDs from the Server. Using the REST API commands, you can get these GUIDs.

This extends our example from above, pulling the guid of a Worksheet and replacing it within the TML object.

    # Find the GUID of the Worksheet to switch to
    new_worksheet_name = 'Worksheet We are Switching To'
    ws_guid = ts.worksheet.find_guid(new_worksheet_name)
  
    # You need to specify the original Worksheet name, in case not all Answers use
    # that particular WS. It will only replace where it finds a match
    o_lb_ws_name = 'Original WS'

    # Switch Liveboard to the new worksheet
    lb.update_worksheet_on_all_answers_by_fqn(original_worksheet_name=o_pb_ws_name, new_worksheet_guid_for_fqn=wg_guid)
    
    # Import (upload) to Update (create_new_on_server=False)
    # The GUID of the TML object will be used so the Server knows what to update
    ts.tml.import_tml(tml=lb.tml, create_new_on_server=False)  # Set to True to create a new Liveboard

Every TML class (see section below) has methods for swapping in FQNs in place of the 'pretty names'. There is an example called `tml_create_new_from_existing.py` which shows a full process of remapping from Tables to Worksheets through Liveboards and Answers. 


### Note on JOINs (POSSIBLY DEPRECATED)
JOINs between tables in ThoughtSpot are objects in the system that exist with their own unique IDs. At the current time, they are named automatically and the names are not unique by default.

To ensure that TML publishing works, you should manually add some type of random number or alphanumeric to the end of the automatically generated JOIN name so that every JOIN has a unique name.

Ex. If you have a JOIN named "DIM_TABLE_1_DIM_TABLE_2", press "Edit" and rename to: "DIM_TABLE_1_DIM_TABLE_2_z1Tl" or some other pattern that guarantees uniqueness.
