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

    def _first_level_property(self, property_key):
        if property_key in self.content:
            return self.content[property_key]
        return None

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

    @property
    def description(self):
        key = "description"
        return self._first_level_property(key)

    @description.setter
    def description(self, new_value: str):
        key = "description"
        self.content[key] = new_value


class View(TML):
    def __init__(self, tml_dict: Dict):
        super().__init__(tml_dict=tml_dict)
    pass


class Table(TML):
    def __init__(self, tml_dict: Dict):
        super().__init__(tml_dict=tml_dict)

    @property
    def db_name(self):
        key = "db"
        return self._first_level_property(key)

    @db_name.setter
    def db_name(self, new_value: str):
        key = "db"
        self.content[key] = new_value

    @property
    def schema(self):
        key = "schema"
        return self._first_level_property(key)

    @schema.setter
    def schema(self, new_value: str):
        key = "schema"
        self.content[key] = new_value

    @property
    def db_table(self):
        key = "db_table"
        return self._first_level_property(key)

    @db_table.setter
    def db_table(self, new_value: str):
        key = "db_table"
        self.content[key] = new_value

    @property
    def connection(self):
        if "connection" in self.content:
            return self.content["connection"]
        else:
            return None

    @property
    def connection_name(self):
        first_level_key = "connection"
        second_level_key = "name"
        if second_level_key in self.content[first_level_key]:
            return self.content[first_level_key][second_level_key]
        else:
            return None

    @connection_name.setter
    def connection_name(self, new_value: str):
        first_level_key = "connection"
        second_level_key = "name"
        self.content[first_level_key][second_level_key] = new_value

    @property
    def connection_type(self):
        first_level_key = "connection"
        second_level_key = "type"
        if second_level_key in self.content[first_level_key]:
            return self.content[first_level_key][second_level_key]
        else:
            return None

    @connection_type.setter
    def connection_type(self, new_value: str):
        first_level_key = "connection"
        second_level_key = "type"
        self.content[first_level_key][second_level_key] = new_value

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
