from typing import Optional, Dict

# TML class works on TML as a Python Dict structure (i.e. the result of a JSON.loads()


class TML:
    def __init__(self, tml_dict: Dict):
        self.tml = tml_dict
        self.guid = tml_dict["guid"]
        self.content_type = None
        # TML file outer is always a guid, then the type of Object being modeled
        for key in self.tml:
            if key == "guid":
                continue
            else:
                self.content_type = key

    @property
    def content(self):
        if self.content_type in self.tml:
            return self.tml[self.content_type]
        else:
            return None

    @property
    def content_name(self):
        if "name" in self.tml[self.content_type]:
            return self.tml[self.content_type]["name"]
        else:
            return None

    @content_name.setter
    def content_name(self, new_name: str):
        self.content["name"] = new_name


class Worksheet(TML):
    def __init__(self, tml_dict: Dict):
        super().__init__(tml_dict=tml_dict)
    pass


class View(TML):
    def __init__(self, tml_dict: Dict):
        super().__init__(tml_dict=tml_dict)
    pass


class Table(TML):
    def __init__(self, tml_dict: Dict):
        super().__init__(tml_dict=tml_dict)

    @property
    def db_name(self):
        if "db" in self.content:
            return self.content["db"]
        return None

    @db_name.setter
    def db_name(self, new_name: str):
        self.content["db"] = new_name

    @property
    def schema(self):
        if "schema" in self.content:
            return self.content["schema"]
        else:
            return None

    @schema.setter
    def schema(self, new_schema: str):
        self.content["schema"] = new_schema

    @property
    def db_table(self):
        if "db_table" in self.content:
            return self.content["db_table"]
        else:
            return None

    @db_table.setter
    def db_table(self, new_db_table: str):
        self.content["db_table"] = new_db_table

    @property
    def connection(self):
        if "connection" in self.content:
            return self.content["connection"]
        else:
            return None

    @property
    def connection_name(self):
        if "name" in self.content["connection"]:
            return self.content["connection"]["name"]
        else:
            return None

    @connection_name.setter
    def connection_name(self, new_connection_name: str):
        self.content["connection"]["name"] = new_connection_name

    @property
    def connection_type(self):
        if "type" in self.content["connection"]:
            return self.content["connection"]["type"]
        else:
            return None

    @connection_type.setter
    def connection_type(self, new_connection_type: str):
        self.content["connection"]["type"] = new_connection_type

    @property
    def columns(self):
        return self.content["columns"]


class Answer(TML):
    def __init__(self, tml_dict: Dict):
        super().__init__(tml_dict=tml_dict)
    pass


class Pinboard(TML):
    def __init__(self, tml_dict: Dict):
        super().__init__(tml_dict=tml_dict)

    @property
    def visualizations(self):
        # Should these be "Answer" objects
        return self.content["visualizations"]
