import os
import requests.exceptions

from tsrest import TSRestV1, MetadataNames, ShareModes

# The purpose of this is to show basic API workflows and how they are accomplished using the TSRestV1 class

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: TSRestV1 = TSRestV1(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

# User Listing
users = ts.get_users()
user = ts.get_users(filter="a_username")

# Group Listing
groups = ts.get_groups()
group = ts.get_groups(filter='a Group')

# Users in a Group


# User Update

# User Creation



# Group Creation