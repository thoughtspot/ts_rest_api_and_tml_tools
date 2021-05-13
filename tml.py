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
        return self.tml[self.content_type]

    @property
    def content_name(self):
        return self.tml[self.content_type]["name"]

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
        return self.content["db"]

    @property
    def schema(self):
        return self.content["schema"]

    @property
    def db_table(self):
        return self.content["db_table"]

    @property
    def connection(self):
        return self.content["connection"]

    @property
    def connection_name(self):
        return self.content["connection"]["name"]

    @property
    def connection_type(self):
        return self.content["connection"]["type"]

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
