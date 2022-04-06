from thoughtspot_rest_api_v1 import *
from endpoint_method_classes import *


#
# For most use cases, a user would use the ThoughtSpot object, which does allow for accessing the direct
# API calls via the .tsrest object
#
class ThoughtSpot:
    def __init__(self, server_url: str):
        self.tsrest = TSRestApiV1(server_url=server_url)
        self.user = UserMethods(self.tsrest)
        self.group = GroupMethods(self.tsrest)
        self.tml = TMLMethods(self.tsrest)
        self.pinboard = PinboardMethods(self.tsrest)
        self.liveboard = LiveboardMethods(self.tsrest)
        self.answer = AnswerMethods(self.tsrest)
        self.connection = ConnectionMethods(self.tsrest)
        self.worksheet = WorksheetMethods(self.tsrest)
        self.table = TableMethods(self.tsrest)
        self.tag = TagMethods(self.tsrest)

    def login(self, username: str, password: str):
        return self.tsrest.session_login(username=username, password=password)

    def logout(self):
        return self.tsrest.session_logout()
