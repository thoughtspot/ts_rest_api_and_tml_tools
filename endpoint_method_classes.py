from thoughtspot_rest_api_v1 import *
from typing import Optional, Dict, List
import typing
#
# Each of these classes is used as an object within the main wrapper class
# to provide a structure based on the object types available within ThoughtSpot
# Any given class may call to various APIs to accomplish the goal specific to that object type
#


class SharedEndpointMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest
        # Each endpoint should override within its own
        self.metadata_name = None
        self.metadata_subtype = None

        # Cache to reduce API calls
        self.last_details = None

    def list(self, sort: str = 'DEFAULT', sort_ascending: bool = True, filter: Optional[str] = None,
             tags_filter: Optional[List[str]] = None, batchsize=-1, offset=-1):
        if self.metadata_subtype is None:
            return self.rest.metadata_listobjectheaders(object_type=self.metadata_name,
                                                        sort=sort,
                                                        sort_ascending=sort_ascending,
                                                        filter=filter,
                                                        tagname=tags_filter,
                                                        batchsize=batchsize,
                                                        offset=offset)
        else:
            return self.rest.metadata_listobjectheaders(object_type=self.metadata_name,
                                                        subtypes=[self.metadata_subtype],
                                                        sort=sort,
                                                        sort_ascending=sort_ascending,
                                                        filter=filter,
                                                        tagname=tags_filter,
                                                        batchsize=batchsize,
                                                        offset=offset)

    def find_guid(self, name: str) -> str:
        objects = self.list(filter=name)
        # Filter is case-insensitive and the equivalent of a wild-card, so need to look for exact match
        # on the response
        for o in objects:
            if o['name'] == name:
                return o['id']
        raise LookupError()

    def get_object_by_id(self, guid):
        id_list = self.rest.metadata_listobjectheaders(object_type=self.metadata_name, fetchids=[guid])
        return id_list[0]

    def details(self, guid: str) -> Dict:

        # Use cache if it exists and matches
        if self.last_details is not None and self.last_details["storables"][0]['header']['id'] == guid:
            details = self.last_details
        else:
            details = self.rest.metadata_details(object_type=self.metadata_name, object_guids=[guid, ])
        self.last_details = details
        return details

    def assign_tags(self, object_guids: List[str], tag_guids: List[str]):
        obj_type = self.metadata_name
        # The API requires a List with the content for each item
        obj_type_list = []
        for o in object_guids:
            obj_type_list.append(obj_type)

        response = self.rest.metadata_assigntag(object_guids=object_guids, object_type=obj_type_list, tag_guids=tag_guids)
        return response

    def share(self, object_guids: List, permissions: Dict):
        response = self.rest.security_share(shared_object_type=self.metadata_name, shared_object_guids=object_guids,
                                            permissions=permissions)
        return response

    def create_share_permissions(self, read_only_users_or_groups_guids: Optional[List[str]] = (),
                                 edit_access_users_or_groups_guids: Optional[List[str]] = (),
                                 remove_access_users_or_groups_groups: Optional[List[str]] = ()) -> Dict:
        permissions_dict = self.rest.get_sharing_permissions_dict()
        for a in read_only_users_or_groups_guids:
            self.rest.add_permission_to_dict(permissions_dict=permissions_dict, guid=a, share_mode=ShareModes.READ_ONLY)
        for a in edit_access_users_or_groups_guids:
            self.rest.add_permission_to_dict(permissions_dict=permissions_dict, guid=a, share_mode=ShareModes.EDIT)
        for a in remove_access_users_or_groups_groups:
            self.rest.add_permission_to_dict(permissions_dict=permissions_dict, guid=a, share_mode=ShareModes.NO_ACCESS)
        return permissions_dict

    def transfer_object_ownership(self, object_guids: List[str], current_owner_username: str, new_owner_username: str):
        if object_guids is None:
            raise Exception()
        self.rest.user_transfer_ownership(current_owner_username=current_owner_username,
                                          new_owner_username=new_owner_username, object_guids=object_guids)


class UserMethods(SharedEndpointMethods):
    def __init__(self, tsrest: TSRestApiV1):
        super().__init__(tsrest)
        self.metadata_name = TSTypes.USER
        # Cache to reduce API calls
        self.last_user_details = None

    def get_user_name_by_id(self, user_guid):
        user = self.get_object_by_id(guid=user_guid)
        return user['name']

    def list_available_objects_for_user(self, user_guid: str, minimum_access_level: str = 'READ_ONLY',
                                        filter: Optional[str] = None):
        return self.rest.metadata_listas(user_or_group_guid=user_guid,
                                         user_or_group=TSTypes.USER,
                                         minimum_access_level=minimum_access_level,
                                         filter=filter)

    def details_all_users(self) -> List:
        # user_get with no filter returns a List of Dicts
        details = self.rest.user_get()
        return details

    def details(self, guid: Optional[str] = None, username: Optional[str] = None):
        # Use cache if it exists and matches
        if self.last_details is not None and self.last_details['header']['id'] == guid:
            details = self.last_details
        else:
            details = self.rest.user_get(user_id=guid, name=username)
        self.last_details = details

        return details

    def privileges_for_user(self, user_guid: str) -> List[str]:
        details = self.details(guid=user_guid)
        return details['privileges']

    def assigned_groups_for_user(self, user_guid: str) -> List[str]:
        details = self.details(guid=user_guid)
        return details['assignedGroups']

    def inherited_groups_for_user(self, user_guid: str) -> List[str]:
        details = self.details(guid=user_guid)
        return details['inheritedGroups']

    def state_of_user(self, user_guid: str) -> str:
        details = self.details(guid=user_guid)
        return details['state']

    def is_user_superuser(self, user_guid: str) -> bool:
        details = self.details(guid=user_guid)
        return details['isSuperUser']

    def user_info(self, user_guid: str) -> Dict:
        details = self.details(guid=user_guid)
        return details['header']

    def user_display_name(self, user_guid: str) -> str:
        details = self.details(guid=user_guid)
        return details['header']['displayName']

    def username_from_guid(self, user_guid: str) -> str:
        details = self.details(guid=user_guid)
        return details['header']['name']

    def user_created_timestamp(self, user_guid: str) -> int:
        details = self.details(guid=user_guid)
        return details['header']['created']

    def user_last_modified_timestamp(self, user_guid: str) -> int:
        details = self.details(guid=user_guid)
        return details['header']['modified']

    # Used when a user should be removed from the system but their content needs to be reassigned to a new owner
    def transfer_ownership_of_all_objects_between_users(self, current_owner_username, new_owner_username):
        return self.rest.user_transfer_ownership(current_owner_username=current_owner_username,
                                                 new_owner_username=new_owner_username)

    @staticmethod
    def get_user_element_for_user_sync(username: str,
                                       display_name: str,
                                       description: Optional[str] = "",
                                       created_epoch: Optional[int] = None,
                                       modified_epoch: Optional[int] = None,
                                       email:str = None,
                                       group_names: Optional[List[str]] = None,
                                       visibility: str = 'DEFAULT') -> Dict:
        response_dict = {
            "name": username,
            "displayName": display_name,
            "principalTypeEnum": "LOCAL_USER",
            "visibility": visibility
        }
        if email is not None:
            response_dict["mail"] = email
        if description is not None:
            response_dict["description"] = description
        if created_epoch is not None:
            response_dict["created"] = created_epoch
        if modified_epoch is not None:
            response_dict["modified"] = modified_epoch
        if group_names is not None:
            response_dict["groupNames"] = group_names

        return response_dict


class GroupMethods(SharedEndpointMethods):
    def __init__(self, tsrest: TSRestApiV1):
        super().__init__(tsrest)
        self.metadata_name = TSTypes.GROUP

    def get_user_name_by_id(self, group_guid):
        group = self.get_object_by_id(guid=group_guid)
        return group['name']

    # This endpoint is under session/ as the root which makes it hard to find in the listings
    def list_users_in_group(self, group_guid: str):
        return self.rest.group_listuser(group_guid=group_guid)

    def list_available_objects_for_group(self, group_guid: str, minimum_access_level: str = 'READ_ONLY',
                                        filter: Optional[str] = None):
        return self.rest.metadata_listas(user_or_group_guid=group_guid,
                                         user_or_group=TSTypes.GROUP,
                                         minimum_access_level=minimum_access_level,
                                         filter=filter)

    def details_all_groups(self) -> List:
        return self.rest.group_get()

    def details(self, guid: Optional[str] = None, name: Optional[str] = None) -> Dict:
        # Use cache if it exists and matches
        if self.last_details is not None and self.last_details['header']['id'] == guid:
            details = self.last_details
        else:
            details = self.rest.group_get(group_guid=guid, name=name)
        self.last_details = details

        return details

    def privileges_for_group(self, group_guid: str):
        details = self.details(guid=group_guid)
        return details['privileges']

    # Does this even make sense?
    def assigned_groups_for_group(self, group_guid: str):
        details = self.details(guid=group_guid)
        return details['assignedGroups']

    def inherited_groups_for_group(self, group_guid: str):
        details = self.details(guid=group_guid)
        return details['inheritedGroups']

    #
    # Unconfirmed, pending more documentation
    #
    def add_privilege_to_group(self, privilege: str, group_name: str):
        return self.rest.group_addprivilege(privilege=privilege, group_names=group_name)

    #
    # Unconfirmed, pending more documentation
    #
    def remove_privilege_from_group(self, privilege: str, group_name: str):
        return self.rest.group_removeprivilege(privilege=privilege, group_names=[group_name,])

    @staticmethod
    def get_group_element_for_user_sync(group_name: str,
                                        display_name: str,
                                        description: Optional[str] = None,
                                        created_epoch: Optional[int] = None,
                                        modified_epoch: Optional[int] = None,
                                        email: str = None,
                                        group_names: Optional[List[str]] = None,
                                        visibility: str = 'DEFAULT') -> Dict:
        response_dict = {
            "name": group_name,
            "displayName": display_name,
            "principalTypeEnum": "LOCAL_GROUP",
            "visibility": visibility
        }
        if email is not None:
            response_dict["mail"] = email
        if description is not None:
            response_dict["description"] = description
        if created_epoch is not None:
            response_dict["created"] = created_epoch
        if modified_epoch is not None:
            response_dict["modified"] = modified_epoch
        if group_names is not None:
            response_dict["groupNames"] = group_names

        return response_dict


class PinboardMethods(SharedEndpointMethods):
    def __init__(self, tsrest: TSRestApiV1):
        super().__init__(tsrest)
        self.metadata_name = TSTypes.PINBOARD

    def pinboard_info(self, pinboard_guid: str) -> Dict:
        details = self.details(guid=pinboard_guid)
        return details["storables"][0]['header']

    # Doesn't even make sense for a Pinboard/Liveboard, commenting out
    #def get_dependent_objects(self, pinboard_guids: List[str]):
        # July Cloud feature
    #    return self.rest.dependency_logicaltable(logical_table_guids=pinboard_guids)

    # SpotIQ analysis is just a Pinboard with property 'isAutocreated': True. 'isAutoDelete': true initially, but
    # switches if you have saved. This may change in the future
    def list_spotiqs(self, unsaved_only: bool = False, sort: str = 'DEFAULT', sort_ascending: bool = True,
                      filter: Optional[str] = None):
        full_listing = self.rest.metadata_listobjectheaders(object_type=TSTypes.PINBOARD,
                                                            sort=sort,
                                                            sort_ascending=sort_ascending,
                                                            filter=filter)
        final_list = []
        for pb in full_listing:
            if pb['isAutoCreated'] is True:
                if unsaved_only is True:
                    if pb["isAutoDelete"] is True:
                        final_list.append(pb)
                else:
                    final_list.append(pb)
        return final_list

    def share_pinboards(self, shared_pinboard_guids: List[str], permissions: Dict,
                       notify_users: Optional[bool] = False, message: Optional[str] = None,
                       email_shares: Optional[List[str]] = None, use_custom_embed_urls: bool = False):
        self.rest.security_share(shared_object_type=TSTypes.PINBOARD,
                                 shared_object_guids=shared_pinboard_guids,
                                 permissions=permissions,
                                 notify_users=notify_users,
                                 message=message,
                                 email_shares=email_shares,
                                 use_custom_embed_urls=use_custom_embed_urls)

    def pdf_export(self, pinboard_id: str,
                         one_visualization_per_page: bool = False,
                         landscape_or_portrait="LANDSCAPE",
                         cover_page: bool = True, logo: bool = True,
                         page_numbers: bool = False, filter_page: bool = True,
                         truncate_tables: bool = False,
                         footer_text: str = None,
                         visualization_ids: List[str] = None):
        return self.rest.export_pinboard_pdf(pinboard_id=pinboard_id,
                                             one_visualization_per_page=one_visualization_per_page,
                                             landscape_or_portrait=landscape_or_portrait,
                                             cover_page=cover_page,
                                             page_numbers=page_numbers,
                                             truncate_tables=truncate_tables,
                                             footer_text=footer_text,
                                             visualization_ids=visualization_ids)

    # The metadata/details call details the connected data sources on a Pinboard, but it is a very complex response to parse
    def get_referenced_data_sources(self, guid):
        details = self.details(guid=guid)
        # Once you get to the resolvedObjects part of the response, you have to iterate because the keys are the
        # GUIDs of each answer on the pinboard
        for ro in details["storables"][0]['header']['resolvedObjects']:
            tables = details["storables"][0]['header']['resolvedObjects'][ro]['reportContent']["sheets"][0]['sheetContent']['visualizations'][0]['vizContent']['columns'] #['column'] ## ['referencedTableHeaders']
            # can be multiple columns
            # each column may or may not have a 'column' key to get to its inner contents
            print(len(tables))
            print(tables)

    def get_all_level_referenced_data_sources(self, guid):
        details = self.details(guid=guid)


# Liveboard is renaming of Pinboard. Most APIs have not changed naming
class LiveboardMethods(PinboardMethods):

    def liveboard_info(self, liveboard_guid: str) -> Dict:
        return self.pinboard_info(pinboard_guid=liveboard_guid)

    def share_liveboards(self, shared_liveboard_guids: List[str], permissions: Dict,
                       notify_users: Optional[bool] = False, message: Optional[str] = None,
                       email_shares: Optional[List[str]] = None, use_custom_embed_urls: bool = False):
        self.rest.security_share(shared_object_type=TSTypes.LIVEBOARD,
                                 shared_object_guids=shared_liveboard_guids,
                                 permissions=permissions,
                                 notify_users=notify_users,
                                 message=message,
                                 email_shares=email_shares,
                                 use_custom_embed_urls=use_custom_embed_urls)


class AnswerMethods(SharedEndpointMethods):
    def __init__(self, tsrest: TSRestApiV1):
        super().__init__(tsrest)
        self.metadata_name = TSTypes.ANSWER

    def share_answers(self, shared_answer_guids: List[str], permissions: Dict,
                       notify_users: Optional[bool] = False, message: Optional[str] = None,
                       email_shares: List[str] = None, use_custom_embed_urls: bool = False):
        self.rest.security_share(shared_object_type=TSTypes.ANSWER,
                                 shared_object_guids=shared_answer_guids,
                                 permissions=permissions,
                                 notify_users=notify_users,
                                 message=message,
                                 email_shares=email_shares,
                                 use_custom_embed_urls=use_custom_embed_urls)


class WorksheetMethods(SharedEndpointMethods):
    def __init__(self, tsrest: TSRestApiV1):
        super().__init__(tsrest)
        self.metadata_name = TSTypes.WORKSHEET
        self.metadata_subtype = MetadataSubtypes.WORKSHEET

    def get_dependent_objects(self, worksheet_guids: List[str]):
        # July Cloud feature
        # Using dependency_listdependents because it is available in 7.1.1 and Cloud
        return self.rest.dependency_listdependents(object_type=TSTypes.WORKSHEET, guids=worksheet_guids)
        # return self.rest.dependency_logicaltable(logical_table_guids=worksheet_guids)

    def get_dependent_pinboards_for_worksheet(self, worksheet_guid: str) -> List:
        dependents = self.get_dependent_objects(worksheet_guids=[worksheet_guid])
        pinboards = []
        for d in dependents:
            pbs = dependents[d][TSTypes.PINBOARD]
            for pb in pbs:
                pinboards.append(pb)
        return pinboards

    def get_dependent_liveboards_for_worksheet(self, worksheet_guid: str) -> List:
        return self.get_dependent_pinboards_for_worksheet(worksheet_guid=worksheet_guid)

    def get_dependent_answers_for_worksheet(self, worksheet_guid: str) -> List:
        dependents = self.get_dependent_objects(worksheet_guids=[worksheet_guid])
        answers_list = []
        for d in dependents:
            answers = dependents[d][TSTypes.ANSWER]
            for a in answers:
                answers_list.append(a)
        return answers_list


class ConnectionMethods(SharedEndpointMethods):
    def __init__(self, tsrest: TSRestApiV1):
        super().__init__(tsrest)
        self.metadata_name = TSTypes.CONNECTION

    # After July Cloud release, override list() to use connection/list vs. metadata/listobjectheaders
    #

    def list_tables_for_connection(self, connection_guid: str, tags_filter: Optional[List[str]] = None) -> List:
        conn_details = self.rest.connection_detail(connection_guid=connection_guid, tagname=tags_filter)
        tables_for_conn = []
        for a in conn_details['tables']:
            if a['header']['type'] == MetadataSubtypes.TABLE:
                tables_for_conn.append(a['header']['id'])
        return tables_for_conn


class TableMethods(SharedEndpointMethods):
    def __init__(self, tsrest: TSRestApiV1):
        super().__init__(tsrest)
        self.metadata_name = TSTypes.TABLE
        self.metadata_subtype = MetadataSubtypes.TABLE

    def find_guid(self, name: str, connection_guid: Optional[str] = None):
        tables = self.list(filter=name)
        # Filter is case-insensitive and the equivalent of a wild-card, so need to look for exact match
        # on the response
        # Additionally, tables can have the same name, so you really need the Connection GUID
        if connection_guid is not None:
            for t in tables:
                if t['name'] == name and t['databaseStripe'] == connection_guid:
                    return t['id']
        elif len(tables) == 1:
            return tables[0]['id']
        else:
            raise LookupError()

    def get_dependent_objects(self, table_guids: List[str]):
        # July Cloud feature
        # Using dependency_listdependents because it is available in 7.1.1 and Cloud
        return self.rest.dependency_listdependents(object_type=TSTypes.TABLE, guids=table_guids)
        #return self.rest.dependency_logicaltable(logical_table_guids=table_guids)

    def get_dependent_worksheets_for_table(self, table_guid: str) -> List:
        dependents = self.get_dependent_objects(table_guids=[table_guid])
        worksheets = []
        for d in dependents:
            logical_tables = dependents[d][TSTypes.TABLE]
            for l in logical_tables:
                if l['type'] == MetadataSubtypes.WORKSHEET:
                    #print(l['id'], l['name'], l['type'])
                    worksheets.append(l)
        return worksheets


#class ViewMethods(SharedEndpointMethods):
#    def __init__(self, tsrest: TSRestApiV1):
#        super().__init__(tsrest)
#        self.metadata_name = TSTypes.TABLE
#        self.metadata_subtype = MetadataSubtypes.VIEW
#
#    def get_dependent_objects(self, view_guids: List[str]):
#        # July Cloud feature
#        # Using dependency_listdependents because it is available in 7.1.1 and Cloud
#        return self.rest.dependency_listdependents(object_type=TSTypes.WORKSHEEET, guids=view_guids)
#        #return self.rest.dependency_logicaltable(logical_table_guids=table_guids)


class TagMethods(SharedEndpointMethods):
    def __init__(self, tsrest: TSRestApiV1):
        super().__init__(tsrest)
        self.metadata_name = TSTypes.TAG

    def assign_tags(self, object_guids: List[str], tag_guids: List[str]):
        # Can't assign tags
        raise Exception()


class TMLMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest
    #
    # Retrieving TML from the Server
    #
    def export_tml(self, guid: str, formattype='JSON') -> "typing.OrderedDict":
        return self.rest.metadata_tml_export(guid=guid)

    # Synonym for export
    def download_tml(self, guid: str, formattype='YAML') -> "typing.OrderedDict":
        return self.rest.metadata_tml_export(guid=guid)

    def export_tml_string(self, guid: str, formattype='YAML') -> str:
        return self.rest.metadata_tml_export_string(guid=guid, formattype=formattype)

    def download_tml_to_file(self, guid: str, filename: str, formattype='YAML', overwrite=True) -> str:
        tml = self.rest.metadata_tml_export_string(guid=guid, formattype=formattype)

        with open(filename, 'w', encoding='utf-8') as fh:
            fh.write(tml)
        return filename

    #
    # Pushing TML to the Server
    #
    def import_tml(self, tml: Dict, create_new_on_server=False, validate_only=False, formattype='JSON'):
        return self.rest.metadata_tml_import(tml=tml, create_new_on_server=create_new_on_server,
                                             validate_only=validate_only, formattype=formattype)

    #def import_tml_from_file(self, filename, create_new_on_server=False, validate_only=False, formattype='YAML'):
    #    with open(filename, 'r') as fh:
    #        tml_str = fh.read()
    #        self.rest.metadata_tml_import(tml=tml_str, create_new_on_server=create_new_on_server,
    #                                     validate_only=validate_only, formattype=formattype)

    # Synonym for import
    def upload_tml(self, tml, create_new_on_server=False, validate_only=False, formattype='JSON'):
        return self.import_tml(tml=tml, create_new_on_server=create_new_on_server,
                               validate_only=validate_only, formattype=formattype)

    def publish_new(self, tml, formattype='JSON'):
        return self.import_tml(tml=tml, create_new_on_server=True,
                               validate_only=False, formattype=formattype)

    def get_guid_from_import_response(self, response):
        return response['object'][0]['response']['header']['id_guid']

    def did_import_succeed(self, response) -> bool:
        # Should respond with 'OK' or 'ERROR'
        status_code = response['object'][0]['response']['status']['status_code']
        if status_code == 'OK':
            return True
        else:
            return False