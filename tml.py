from typing import Optional, Dict
from enum import Enum, auto
# TML class works on TML as a Python Dict structure (i.e. the result of a JSON.loads()


class TML:
    def __init__(self, tml_dict: Dict):
        self.tml = tml_dict
        # Answers within a Pinboard just have an "id"
        if 'guid' in tml_dict:
            self.guid = tml_dict["guid"]
        elif 'id' in tml_dict:
            self.guid = tml_dict["id"]
        else:
            raise Exception()
        self.content_type = None
        # TML file outer is always a guid, then the type of Object being modeled
        for key in self.tml:
            if key in ["guid", "id"]:
                continue
            else:
                self.content_type = key

    def _first_level_property(self, property_key):
        if property_key in self.content:
            return self.content[property_key]
        return None

    def _second_level_property(self, first_level_key, second_level_key):
        if second_level_key in self.content[first_level_key]:
            return self.content[first_level_key][second_level_key]
        else:
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

    @property
    def properties(self):
        key = "properties"
        return self.content[key]

    @property
    def is_bypass_rls_flag(self):
        first_level_key = "properties"
        second_level_key = "is_bypass_rls"
        return self._second_level_property(first_level_key, second_level_key)

    @is_bypass_rls_flag.setter
    def is_bypass_rls_flag(self, new_value: bool):
        first_level_key = "properties"
        second_level_key = "is_bypass_rls"
        self.content[first_level_key][second_level_key] = str(new_value).lower()

    @property
    def join_progressive_flag(self):
        first_level_key = "properties"
        second_level_key = "join_progressive"
        return self._second_level_property(first_level_key, second_level_key)

    @join_progressive_flag.setter
    def join_progressive_flag(self, new_value: bool):
        first_level_key = "properties"
        second_level_key = "join_progressive"
        self.content[first_level_key][second_level_key] = str(new_value).lower()

    @property
    def tables(self):
        key = "tables"
        return self._first_level_property(key)

    @property
    def joins(self):
        key = "joins"
        return self._first_level_property(key)

    @property
    def table_paths(self):
        key = "table_paths"
        return self._first_level_property(key)

    def update_table(self, original_table_name: str, new_table_guid: str):
        tables = self.tables
        for t in tables:
            if t["name"] == original_table_name:
                # Add fqn reference to point to new worksheet
                t["fqn"] = new_table_guid
                # Change id to be previous name
                t["id"] = t["name"]
                # Remove the original name parameter
                del t["name"]


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

        class ChartTypes:
            COLUMN = 'COLUMN'
            BAR = 'BAR'
            LINE = 'LINE'
            PIE = 'PIE'
            SCATTER = 'SCATTER'
            BUBBLE = 'BUBBLE'
            STACKED_COLUMN = 'STACKED_COLUMN'
            AREA = 'AREA'
            PARETO = 'PARETO'
            GEO_AREA = 'GEO_AREA'
            GEO_BUBBLE = 'GEO_BUBBLE'
            GEO_HEATMAP = 'GEO_HEATMAP'
            GEO_EARTH_BAR = 'GEO_EARTH_BAR'
            GEO_EARTH_AREA = 'GEO_EARTH_AREA'
            GEO_EARTH_GRAPH = 'GEO_EARTH_GRAPH'
            GEO_EARTH_BUBBLE = 'GEO_EARTH_BUBBLE'
            GEO_EARTH_HEATMAP = 'GEO_EARTH_HEATMAP'
            WATERFALL = 'WATERFALL'
            TREEMAP = 'TREEMAP'
            HEATMAP = 'HEATMAP'
            STACKED_AREA = 'STACKED_AREA'
            LINE_COLUMN = 'LINE_COLUMN'
            FUNNEL = 'FUNNEL'
            LINE_STACKED_COLUMN = 'LINE_STACKED_COLUMN'
            PIVOT_TABLE = 'PIVOT_TABLE'
            SANKEY = 'SANKEY'
            GRID_TABLE = 'GRID_TABLE'
            SPIDER_WEB = 'SPIDER_WEB'
            WHISKER_SCATTER = 'WHISKER_SCATTER'
            STACKED_BAR = 'STACKED_BAR'
            CANDLESTICK = 'CANDLESTICK'
        self.CHART_TYPES = ChartTypes

    @property
    def description(self):
        key = "description"
        return self._first_level_property(key)

    @description.setter
    def description(self, new_value: str):
        key = "description"
        self.content[key] = new_value

    @property
    def display_mode(self):
        key = "display_mode"
        return self._first_level_property(key)

    @display_mode.setter
    def display_mode(self, new_value: str):
        key = "display_mode"
        self.content[key] = new_value

    # Helper functions since the values are non-obvious
    def set_chart_mode(self):
        self.display_mode = 'CHART_MODE'

    def set_table_mode(self):
        self.display_mode = 'TABLE_MODE'

    @property
    def search_query(self):
        key = "search_query"
        return self._first_level_property(key)

    @search_query.setter
    def search_query(self, new_value: str):
        key = "search_query"
        self.content[key] = new_value

    @property
    def answer_columns(self):
        key = "answer_columns"
        return self._first_level_property(key)

    @property
    def tables(self):
        key = "tables"
        return self._first_level_property(key)

    @property
    def formulas(self):
        key = "formulas"
        return self._first_level_property(key)

    @property
    def chart(self):
        key = "chart"
        return self._first_level_property(key)

    # There is an 'fqn' parameter to use when replacing a worksheet reference
    def update_worksheet(self, original_worksheet_name: str, new_worksheet_guid: str):
        tables = self.tables
        for t in tables:
            if t["name"] == original_worksheet_name:
                # Add fqn reference to point to new worksheet
                t["fqn"] = new_worksheet_guid
                # Change id to be previous name
                t["id"] = t["name"]
                # Remove the original name parameter
                del t["name"]

    # Allows for multiple mappings to be sent in
    def update_worksheets(self, orig_worksheet_to_new_guid_dict: Dict[str, str]):
        tables = self.tables
        for t in tables:
            if t["name"] in orig_worksheet_to_new_guid_dict:
                # Add fqn reference to point to new worksheet
                t["fqn"] = orig_worksheet_to_new_guid_dict[t["name"]]
                # Change id to be previous name
                t["id"] = t["name"]
                # Remove the original name parameter
                del t["name"]


class Pinboard(TML):
    def __init__(self, tml_dict: Dict):
        super().__init__(tml_dict=tml_dict)

    @property
    def visualizations(self):
        # Should these be "Answer" objects
        return self.content["visualizations"]

    # Pass through to allow hitting all Answers contained with a single pinboard
    # You can also do this individually if working the objects one by one
    def update_worksheet_on_all_answers(self, original_worksheet_name:str, new_worksheet_guid:str):
        for a in self.visualizations:
            answer = Answer(a)
            answer.update_worksheet(original_worksheet_name=original_worksheet_name,
                                    new_worksheet_guid=new_worksheet_guid)

    def update_worksheets_on_all_answers(self, orig_worksheet_to_new_guid_dict: Dict[str, str]):
        for a in self.visualizations:
            answer = Answer(a)
            answer.update_worksheets(orig_worksheet_to_new_guid_dict=orig_worksheet_to_new_guid_dict)