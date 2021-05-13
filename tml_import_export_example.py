import os
import requests.exceptions

from tsrest import TSRest
from tml import *

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: TSRest = TSRest(server=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

pinboards = ts.get_pinboards()
first_pinboard_id = pinboards[0]["id"]
print("First Pinboard ID: {}".format(first_pinboard_id))

tml = ts.export_tml(guid=first_pinboard_id)
tml_obj = Pinboard(tml)
print("TML loaded")
print(tml_obj.guid)
print(tml_obj.content_type)
print(tml_obj.content_name)
tml_obj.content_name = "Bryant Pinboard"
tml_obj.content["description"] = "I've added a description"
visualizations = tml_obj.visualizations
for v in visualizations:
    print(v["id"])
    print(v)

tables = ts.get_logical_tables()
first_table_id = tables[0]["id"]
print("First Table ID: {}".format(first_table_id))
# print(tml_obj.tml)
table_obj = Table(ts.export_tml(guid=first_table_id))
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

ts.logout()
