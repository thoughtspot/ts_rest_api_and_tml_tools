# ts_rest_api_and_tml_tools
ts_rest_api_and_tml_tools is a functional wrapper library for doing actions with the ThoughtSpot REST API, including flows involving TML.

If you have used this package previously, two previously included components have now been split off into their own modules (`thoughtspot-rest-api-v1` and `thoughtspot-tml`, which can be installed from PyPi using pip. Both modules have been added to the requirements.txt and setup.cfg and should be installed to use ts_rest_api_and_tml_tools.

The `/examples` directory includes examples of many common workflows accomplished with the REST API and/or TML manipulation.

You can use the `thoughtspot-rest-api-v1` module directly to do all the REST API actions. 

The `ThoughtSpot` class simply wraps the calls to `thoughtspot-rest-api-v1` to present methods organized by object type with more obvious and consistent method names.

In essence, the `ThoughtSpot` class imposes more 'structure' on the V1 REST API, which tends to have endpoints that are very flexible but require more arguments to use, particularly around metadata commands.

It is developed by ThoughtSpot CS and SE team members and is not supported by ThoughtSpot support.

The V2 ThoughtSpot REST API is currently in preview. All requests in V2 will be in JSON format, with a complete Playground environment, and there will be SDKs automatically provided in various languages to issue the endpoint commands.

ts_rest_api_and_tml_tools is developed and tested only against ThoughtSpot Cloud using the available tspublic/v1 endpoints. 

It should also work with Software versions 7.1.1 and later, but the library is not versioned, so please check your documentation for available endpoints within the release you use if on a Software release.

All code and examples are intended only as a starting point to be customized to your purposes. Nothing is wrapped up and documented for "production" out of the box.

For a library of tools which includes support for older Software versions of ThoughtSpot and built out command-line utilities, please see https://github.com/thoughtspot/cs_tools . 

## Contents
 - Getting Started
 - Examples directory
 - REST API basics
 - TML & REST API
 - REST API advanced
 

## Getting Started
### Components
- thoughtspot.py provides a class for doing actions to the ThoughtSpot Server, organized with a series of sub-objects which represent the various object types in ThoughtSpot
    - endpoint_method_classes.py is implements the individual classes which are objects under the ThoughtSpot class    

As mentioned in the intro, both `thoughtspot-rest-api-v1` and `thoughtspot-tml` modules are requirements for this package, and are assumed in the examples.

To install the latest versions of the other modules:

    pip install thoughtspot-rest-api-v1 --upgrade
    pip install thoughtspot-tml --upgrade

### Importing the classes
    from thoughtspot import *
    from thoughspot_tml import *

All features from the TSRestApiV1 class in the thoughtspot-rest-api-v1 module are available as the `.tsrest` sub-object from the `ThoughtSpot` class.    

### Modifying the TSRestApiV1 requests.Session object (SSL errors, etc.)
The REST API commands are all handled via the `requests` module, using a `requests.Session` object. 

The session object used by all methods is accessible via:

    ThoughtSpot.tsrest.session

A common issue within organizations is SSL certificates not being available / included within the certificate store used by Python. One way around this issue is to use the `verify=False` argument in requests (this is not recommended, but may be the only easy path forward. Check with your security team and never use with ThoughtSpot Cloud or from outside your protected network).

This will set the Session object to `verify=False` for all calls:

    ts: ThoughtSpot = ThoughtSpot(server=server)
    ts.tsrest.session.verify = False

If you find there are other options you need to set on the Session object for your particular situation, you can use the same technique to apply other changes.

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

## Examples directories

## REST API basics (thoughtspot.py)
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
There is a  `.tsrest` object available under `ThoughtSpot` which is the instantiated `TSRestApiV1` object from the `thoughtspot-rest-api-v1` module that all the other classes use to make the REST API calls. The `login()` and `logout()` methods of `ThoughtSpot` class actually make a call to this internal TSRestApiV1 object.

If you are testing / confirming how the REST API calls work, or want to use options that are not represented by the Endpoint Method Classes, you can directly use `ThoughtSpot.tsrest` to get to all the methods of the `TSRestApiV1` class.

Please see the documentation of `thoughspot-rest-api-v1` here: https://github.com/thoughtspot/thoughtspot_rest_api_v1_python#readme 

### ENUM data structures
The ThoughtSpot API has internal namings for many features, which require looking up in the reference guide. To help out, there are several ENUM style classes:

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

## TML & REST API
ThoughtSpot Modeling Language (TML) is the YAML format for representing ThoughtSpot objects. TML can be exported as YAML or JSON. 

The `thoughspot-tml` module provides classes for manipulating TML files programmatically. Include this module with:

    from thoughtspot_tml import *

The `ThoughtSpot.tml` sub-object presents the REST API TML import/export methods. These accept the `.tml` property of all the classes from `thoughtspot-tml`

### Retrieving the TML as a Python OrderedDict from REST API
If you want to use the TML classes to programmatically adjust the returned TML, there is a `export_tml(guid)` method which retrieves the TML from the API in JSON format and then returns it as a Python OrderedDict, which is the input for classes from `thoughtspot-tml`.

This method is designed to be the input into all of the TML descendant classes
    
    from thoughtspot_tml import *

    lb_tml = ts.tml.export_tml(guid=lb_guid)
    # Create a Liveboard TML object
    lb_obj = Liveboard(lb_tml)
    # Or do it all in one step: 
    lb_obj = Liveboard(ts.tml.export_tml(guid=lb_guid))

### Opening a TML file from disk and loading into a TML class object
The YAMLTML class from `thoughtspot-tml` contains static methods to help with correct import and formatting of ThoughtSpot's TML YAML.
    
    from thoughtspot-tml import *
    
    fh = open('tml_file.worksheet.tml', 'r')
    tml_yaml_str = fh.read()
    fh.close()

    tml_yaml_ordereddict = YAMLTML.load_string(tml_yaml_str)

    tml_obj = Worksheet(tml_yaml_ordereddict)

    tml_obj.description = "Adding a wonderful description to this document"

    modified_tml_string = YAMLTML.dump_tml_object(tml_obj)
    fh = open('modified_tml.worksheet.tml', 'w')
    fh.write(modified_tml_string)

Full example of working with a YAML strings is in `examples/tml_and_sdlc/tml_yaml_intro.py`.

### Downloading the TML directly as string
If you want the TML as you would see it within the TML editor, use
`ThoughtSpot.tml.export_tml_string(guid, formattype)`

or

`ThoughtSpot.tsrest.metadata_tml_export_string(guid, formattype)`

formattype defaults to 'YAML' but can be set to 'JSON'.

This method returns a Python str object, which can then be editing in memory or saved directly to disk. 

Example of saving to disk is available in `examples/tml_and_sdlc/tml_download.py`.

### Importing/Publishing TML back to ThoughtSpot Server
The import_tml() method lets you push the TML Dict back to the Server

The TML OrderedDict is stored as the `.tml` property of any TML class (Worksheet.tml, Answer.tml, etc.). You must reference the `.tml` property when sending into `.import_tml()`

    ThoughtSpot.tml.import_tml(tml, create_new_on_server=False, validate_only=False))

You can also import multiple TML files at the same time by sending a List of the tml dicts:
    
    ThoughtSpot.tml.import_tml([wb_obj_1.tml, wb_obj_2.tml], create_new_on_server=True)

There are a few optional arguments: 
- `create_new_on_server` - you must set this to True, otherwise it will update the existing object with the same GUID.
- `validate_only` - If set to True, this only runs through validation and returns the response with any errors listed'

There is a static method for pulling the GUIDs from the import command response `ts.tsrest.guids_from_imported_tml()`, which returns the GUIDs in a list in the order they were sent to the import.

Example:
    
    from thoughtspot_tml import *

    # Get create Worksheet object
    ws_obj = Worksheet(ts.tml.export_tml(guid=lb_guid))
    # Send the .tml property, not the whole object
    import_response = ts.tml.import_tml(ws_obj.tml, create_new_on_server=False)
    new_guids = ts.tsrest.guids_from_imported_tml(import_response)
    new_guid = new_guids[0]  # when only a single TML imported

NOTE: If you use 'create_new_on_server=True' but are uploading from a TML that has an existing GUID property, use the `.remove_guid()` method on the TML object first, to make sure any old references are cleared and the new object creates successfully.

### TML Objects from thoughtspot-tml module
Please see the `thoughtspot-tml` module documentation available at https://github.com/thoughtspot/thoughtspot_tml#readme for a full guide to each of the TML classes and their methods.

## REST API advanced