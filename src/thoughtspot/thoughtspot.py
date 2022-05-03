from thoughtspot_rest_api_v1 import TSRestApiV1

from .endpoint_method_classes import (
    UserMethods, GroupMethods, TMLMethods, PinboardMethods, LiveboardMethods,
    AnswerMethods, ConnectionMethods, WorksheetMethods, TableMethods, TagMethods
)


class ThoughtSpot:
    """
    A wrapper around the TSRestApiV1 library which provides a friendly UX.

    Attributes
    ----------
    server_url: str
      frontend url of your ThoughtSpot platform
    """
    def __init__(self, server_url: str):
        self.tsrest = TSRestApiV1(server_url=server_url)
        self.answer = AnswerMethods(self.tsrest)
        self.connection = ConnectionMethods(self.tsrest)
        self.group = GroupMethods(self.tsrest)
        self.liveboard = LiveboardMethods(self.tsrest)
        self.pinboard = PinboardMethods(self.tsrest)
        self.table = TableMethods(self.tsrest)
        self.tag = TagMethods(self.tsrest)
        self.tml = TMLMethods(self.tsrest)
        self.worksheet = WorksheetMethods(self.tsrest)
        self.user = UserMethods(self.tsrest)

    def login(self, username: str, password: str) -> bool:
        """
        Log in to your ThoughtSpot cluster.

        Parameters
        ----------
        username : str
          a local account's username

        password : str
          a local account's password
        """
        return self.tsrest.session_login(username=username, password=password)

    def logout(self) -> bool:
        """
        Log out of your ThoughtSpot cluster.
        """
        return self.tsrest.session_logout()
