import re
import os

import oyaml as yaml

from thoughtspot import *
from tml import *

# The default format for TML is YAML
# Viewing TML in the ThoughtSpot UI will always show YAML, as will donwnload from the UI
# The REST API allows for downloading and uploading of TML as JSON or YAML

# The TML library does not care about the input format - it works from a Python OrderedDict object
# At the current time, tsrestapiv1.py library converts the TML library Python object into JSON for upload (automatic)

# This example shows how to use the TML library with the oyaml (expansion on PyYAML to keep the order of the document)
# When used correctly, you can output identical YAML TML to what ThoughtSpot would output,
# allowing programmatically generated or altered TML to match the style from ThoughtSpot


# Function to add export like ThoughtSpot does and double-quote certain tags where necessary
def dump_tml_to_yaml(tml_obj):
    # The width property must be large to not introduce line breaks into long formulas
    dump_yaml_string = yaml.dump(tml_obj.tml, Dumper=yaml.Dumper, width=700)

    # The 'expr' tag in a worksheet is always double-quoted, but PyYAML output does not do
    re_pattern = "(expr: )(.+)\n"

    def double_quote_expr_values(matchobj):
        return '{}"{}"\n'.format(matchobj.group(1), matchobj.group(2))

    final_yaml = re.sub(re_pattern, double_quote_expr_values, dump_yaml_string)
    return final_yaml

# Sign-in to ThoughtSpot Server to use REST API
username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

# Export a TML object as a YAML string
object_guid = ""
tml_yaml_str = ts.tml.export_tml_string(guid=object_guid, formattype='YAML')

# You could instead read a TML file from disk (in Git repository)
# fh = open('tml_file.worksheet.tml', 'r')
# tml_yaml_str = fh.read()
# fh.close()

# Load the YAML string into a Python OrderedDict
tml_yaml_ordereddict = yaml.load(tml_yaml_str, Loader=yaml.Loader)

# Create a TML object for the type ( Table(), Worksheet(), Liveboard(), Answer() )
tml_obj = Worksheet(tml_yaml_ordereddict)

# Modify the object with any of the methods and properties
tml_obj.description = "Adding a wonderful description to this document"

# Export out to disk
modified_tml_string = dump_tml_to_yaml(tml_obj=tml_obj)
fh = open('modified_tml.worksheet.tml', 'w')
fh.write(modified_tml_string)

# Import via REST API
# Remove GUID to create new object
tml_obj.remove_guid()

ts.tml.import_tml(tml=tml_obj.tml, create_new_on_server=True, validate_only=False)