from typing import Optional, Dict, List
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

    def remove_guid(self):
        del self.tml['guid']

    @property
    def guid(self):
        return self.tml['guid']

    @guid.setter
    def guid(self, new_guid: str):
        self.tml['guid'] = new_guid


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

    def change_table_by_fqn(self, original_table_name: str, new_table_guid: str):
        tables = self.tables
        for t in tables:
            if t["name"] == original_table_name:
                # Add fqn reference to point to new worksheet
                t["fqn"] = new_table_guid
                # Change id to be previous name
                t["id"] = t["name"]
                # Remove the original name parameter
                del t["name"]

    def remap_tables_to_new_fqn(self, name_to_fqn_map: Dict):
        # joins_with is an Array of JOIN information
        for a in self.tables:
            table_name = a['name']
            if table_name in name_to_fqn_map:
                a['fqn'] = name_to_fqn_map[table_name]


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

    def replace_connection_name_with_fqn(self, fqn_guid: str):
        first_level_key = "connection"
        second_level_key = "name"
        del self.content[first_level_key][second_level_key]
        self.content[first_level_key]['fqn'] = fqn_guid

    @property
    def columns(self):
        return self.content["columns"]

    # Connection names are unique and thus don't require FQN
    def change_connection_by_name(self, original_connection_name: str, new_connection_name: str):
        c = self.connection
        if self.connection_name == original_connection_name:
            self.connection_name = new_connection_name

    @property
    def joins(self):
        first_level_key = "joins_with"
        return self.content[first_level_key]

    # When publishing a large set of tables, it may not be possible to replicate the JOINs initially because referenced
    # tables may not exist yet from the publishing process. This removes the section, and later you can add them
    def remove_joins(self):
        if 'joins_with' in self.content:
            del self.content['joins_with']

    def remap_joins_to_new_fqn(self, name_to_fqn_map: Dict):
        # joins_with is an Array of JOIN information
        if 'joins_with' in self.content:
            for a in self.content['joins_with']:
                table_name = a['destination']['name']
                if table_name in name_to_fqn_map:
                    a['destination']['fqn'] = name_to_fqn_map[table_name]
                    del a['destination']['name']

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
    def change_worksheet_by_fqn(self, original_worksheet_name: str, new_worksheet_guid_for_fqn: str):
        tables = self.tables
        for t in tables:
            if t["name"] == original_worksheet_name:
                # Add fqn reference to point to new worksheet
                t["fqn"] = new_worksheet_guid_for_fqn
                # Change id to be previous name
                t["id"] = t["name"]
                # Remove the original name parameter
                del t["name"]

    # Allows for multiple mappings to be sent in
    def change_worksheets_by_fqn(self, name_to_guid_map: Dict[str, str]):
        tables = self.tables
        for t in tables:
            if t["name"] in name_to_guid_map:
                # Add fqn reference to point to new worksheet
                t["fqn"] = name_to_guid_map[t["name"]]
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
        if 'visualizations' in self.content:
            return self.content["visualizations"]
        else:
            return []

    @property
    def answers_as_objects(self) -> List[Answer]:
        v = self.visualizations
        answers = []
        for a in v:
            a_obj = Answer(a)
            answers.append(a_obj)
        return answers

    @property
    def layout_tiles(self):
        first_level_key = "layout"
        second_level_key = "tiles"
        return self.content[first_level_key][second_level_key]

    @layout_tiles.setter
    def layout_tiles(self, new_tiles):
        first_level_key = "layout"
        second_level_key = "tiles"
        self.content[first_level_key][second_level_key] = new_tiles

    # Pass through to allow hitting all Answers contained with a single pinboard
    # You can also do this individually if working the objects one by one
    def update_worksheet_on_all_answers_by_fqn(self, original_worksheet_name:str, new_worksheet_guid_for_fqn:str):
        for a in self.visualizations:
            answer = Answer(a)
            answer.change_worksheet_by_fqn(original_worksheet_name=original_worksheet_name,
                                           new_worksheet_guid_for_fqn=new_worksheet_guid_for_fqn)

    def remap_worksheets_to_new_fqn(self, name_to_guid_map: Dict[str, str]):
        for a in self.visualizations:
            answer = Answer(a)
            answer.change_worksheets_by_fqn(name_to_guid_map=name_to_guid_map)