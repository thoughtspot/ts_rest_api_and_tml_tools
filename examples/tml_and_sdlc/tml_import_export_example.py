import os
import requests.exceptions

from thoughtspot import ThoughtSpot
from tml import *

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

pinboards = ts.pinboard.list()
first_pinboard_id = pinboards[3]["id"]
print("First Pinboard ID: {}".format(first_pinboard_id))

# The export_tml returns a Python Dict representation of the response
tml = ts.tml.export_tml(guid=first_pinboard_id)

# You can create a base TML object, which only has the .content and .content_name properties
# tml_obj = TML(tml)
# tml_obj.content["additional_keys"]["sub-keys"]

# But if you know the type of object, then you can use one of the descendant objects to give
# more built in properties to access rather than having to work through the .content property

pb_obj = Pinboard(tml)
print("Pinboard object created")
print(pb_obj.guid)
print(pb_obj.content_type)
print(pb_obj.content_name)
pb_obj.content_name = "New Pinboard Name"
pb_obj.content["description"] = "I've added a description"
visualizations = pb_obj.visualizations
for v in visualizations:
    print(v["id"])
    # print(v)
    a = Answer(v)
    print(a.search_query)
    print(a.display_mode)
    a.set_table_mode()
    a.description = 'Each Answer now is described as thus'
    print(a.chart)
    a.chart["type"] = a.CHART_TYPES.GEO_EARTH_GRAPH
    print(a.chart)

print(pb_obj.tml)
exit()

# To update the existing object, use TSRest.import_tml(tml, create_new_on_server=False) [the default]
#
# ts.import_tml(pb_obj, create_new_on_server=False)

# To create a new object, use TSRest.import_tml(tml, create_new_on_server=True)
# It doesn't matter that the TML object has the original GUID still -- a new one will be created
# because you chose create_new_on_server=True

# ts.import_tml(pb_obj, create_new_on_server=True)

# The following gets a Table, which has the most properties built out currently besides the Pinboard
tables = ts.table.list()
first_table_id = tables[0]["id"]
print("First Table ID: {}".format(first_table_id))
# print(tml_obj.tml)
table_obj = Table(ts.tml.export_tml(guid=first_table_id))
print("Original Table TML object:")
print(table_obj.tml)
print("Table DB name: {}".format(table_obj.db_name))
print("Table name: {}".format(table_obj.db_table))
print("Table connection name: {}".format(table_obj.connection_name))
print("Table connection type: {}".format(table_obj.connection_type))
table_obj.connection_name = 'MarkSpot v2'

print("New Table connection name: {}".format(table_obj.connection_name))
print("Complete TML object now: ")
print(table_obj.tml)

# ts.tml.import_tml(table_obj, create_new_on_server=True)

ts.logout()
