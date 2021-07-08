from tsrestapiv1 import *

#
# Each of these classes is used as an object within the main wrapper class
# to provide a structure based on the object types available within ThoughtSpot
# Any given class may call to various APIs to accomplish the goal specific to that object type
#


class TMLMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest
    #
    # Retrieving TML from the Server
    #
    def export_tml(self, guid: str, formattype='JSON') -> Dict:
        return self.rest.metadata_tml_export(guid=guid, formattype=formattype)

    # Synonym for export
    def download_tml(self, guid: str, formattype='JSON') -> Dict:
        return self.rest.metadata_tml_export(guid=guid, formattype=formattype)

    def export_tml_string(self, guid: str, formattype='JSON') -> str:
        return self.rest.metadata_tml_export_string(guid=guid, formattype=formattype)

    def download_tml_to_file(self, guid: str, filename: str, formattype='YAML', overwrite=True) -> str:
        tml = self.rest.metadata_tml_export_string(guid=guid, formattype=formattype)

        with open(filename, 'w') as fh:
            fh.write(tml)
        return filename

    #
    # Pushing TML to the Server
    #
    def import_tml(self, tml, create_new_on_server=False, validate_only=False, formattype='JSON'):
        return self.rest.metadata_tml_import(tml=tml, create_new_on_server=create_new_on_server,
                                             validate_only=validate_only, formattype=formattype)

    def import_tml_from_file(self, filename, create_new_on_server=False, validate_only=False, formattype='YAML'):
        with open(filename, 'r') as fh:
            tml_str = fh.read()
            self.rest.metadata_tml_import(tml=tml_str, create_new_on_server=create_new_on_server,
                                          validate_only=validate_only, formattype=formattype)

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

class UserMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest
        # Cache to reduce API calls
        self.last_user_details = None

    def list_users(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                   filter: Optional[str] = None, tags_filter: Optional[List[str]] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.USER,
                                                    sort=sort,
                                                    sort_ascending=sort_ascending,
                                                    filter=filter,
                                                    tagname=tags_filter)

    def find_guid(self, name: str) -> str:
        users = self.list_users(filter=name)
        # Filter is case-insensitive and the equivalent of a wild-card, so need to look for exact match
        # on the response
        for u in users:
            if u['name'] == name:
                return u['id']
        raise LookupError()

    def get_user_by_id(self, user_guid):
        # fetchids is JSON array of strings, we are building manually for singular here
        fetchids = '["{}"]'.format(user_guid)
        users_list = self.rest.metadata_listobjectheaders(object_type=MetadataNames.USER, fetchids=fetchids)
        return users_list[0]

    def get_user_name_by_id(self, user_guid):
        user = self.get_user_by_id(user_guid=user_guid)
        return user['name']

    def list_available_objects_for_user(self, user_guid: str, minimum_access_level: str = 'READ_ONLY',
                                        filter: Optional[str] = None):
        return self.rest.metadata_listas(user_or_group_guid=user_guid,
                                         user_or_group=MetadataNames.USER,
                                         minimum_access_level=minimum_access_level,
                                         filter=filter)

    def user_details(self, user_guid: str) -> Dict:
        # Use cache if it exists and matches
        if self.last_user_details is not None and self.last_user_details["storables"][0]['header']['id'] == user_guid:
            details = self.last_user_details
        else:
            details = self.rest.metadata_details(object_type=MetadataNames.USER, object_guids=[user_guid, ])
        self.last_user_details = details
        return details

    def privileges_for_user(self, user_guid: str) -> List[str]:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['privileges']

    def assigned_groups_for_user(self, user_guid: str) -> List[str]:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['assignedGroups']

    def inherited_groups_for_user(self, user_guid: str) -> List[str]:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['inheritedGroups']

    def state_of_user(self, user_guid: str) -> str:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['state']

    def is_user_superuser(self, user_guid: str) -> bool:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['isSuperUser']

    def user_info(self, user_guid: str) -> Dict:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['header']

    def user_display_name(self, user_guid: str) -> str:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['header']['displayName']

    def username_from_guid(self, user_guid: str) -> str:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['header']['name']

    def user_created_timestamp(self, user_guid: str) -> int:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['header']['created']

    def user_last_modified_timestamp(self, user_guid: str) -> int:
        details = self.user_details(user_guid=user_guid)
        return details["storables"][0]['header']['modified']

    # Used when a user should be removed from the system but their content needs to be reassigned to a new owner
    def transfer_ownership_of_objects_between_users(self, current_owner_username, new_owner_username):
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


class GroupMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_groups(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                        filter: Optional[str] = None, tags_filter: Optional[List[str]] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.GROUP,
                                                    sort=sort,
                                                    sort_ascending=sort_ascending,
                                                    filter=filter,
                                                    tagname=tags_filter)

    def find_guid(self, name: str) -> str:
        groups = self.list_groups(filter=name)
        # Filter is case-insensitive and the equivalent of a wild-card, so need to look for exact match
        # on the response
        for g in groups:
            if g['name'] == name:
                return g['id']
        raise LookupError()

    def get_group_by_id(self, group_guid):
        # fetchids is JSON array of strings, we are building manually for singular here
        fetchids = '["{}"]'.format(group_guid)
        groups_list = self.rest.metadata_listobjectheaders(object_type=MetadataNames.GROUP, fetchids=fetchids)
        return groups_list[0]

    def get_user_name_by_id(self, group_guid):
        group = self.get_group_by_id(group_guid=group_guid)
        return group['name']

    # This endpoint is under session/ as the root which makes it hard to find in the listings
    def list_users_in_group(self, group_guid: str):
        return self.rest.session_group_listuser(group_guid=group_guid)

    def list_available_objects_for_group(self, group_guid: str, minimum_access_level: str = 'READ_ONLY',
                                        filter: Optional[str] = None):
        return self.rest.metadata_listas(user_or_group_guid=group_guid,
                                         user_or_group=MetadataNames.GROUP,
                                         minimum_access_level=minimum_access_level,
                                         filter=filter)

    def privileges_for_group(self, group_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.GROUP,
                                             object_guids=[group_guid, ])
        return details["storables"][0]['privileges']

    # Does this even make sense?
    def assigned_groups_for_group(self, group_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.GROUP,
                                             object_guids=[group_guid, ])
        return details["storables"][0]['assignedGroups']

    def inherited_groups_for_group(self, group_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.GROUP,
                                             object_guids=[group_guid, ])
        return details["storables"][0]['inheritedGroups']

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


class PinboardMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_pinboards(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                       filter: Optional[str] = None, tags_filter: Optional[List[str]] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.PINBOARD,
                                                    sort=sort,
                                                    sort_ascending=sort_ascending,
                                                    filter=filter,
                                                    tagname=tags_filter)

    def find_guid(self, name: str) -> str:
        pinboards = self.list_pinboards(filter=name)
        # Filter is case-insensitive and the equivalent of a wild-card, so need to look for exact match
        # on the response
        for p in pinboards:
            if p['name'] == name:
                return p['id']
        raise LookupError()

    def get_pinboard_by_id(self, pinboard_guid):
        # fetchids is JSON array of strings, we are building manually for singular here
        fetchids = '["{}"]'.format(pinboard_guid)
        pinboards_list = self.rest.metadata_listobjectheaders(object_type=MetadataNames.PINBOARD, fetchids=fetchids)
        return pinboards_list[0]

    def pinboard_details(self, pinboard_guid):
        details = self.rest.metadata_details(object_type=MetadataNames.PINBOARD, object_guids=[pinboard_guid,])
        return details

    def pinboard_info(self, pinboard_guid: str) -> Dict:
        details = self.pinboard_details(pinboard_guid=pinboard_guid)
        return details["storables"][0]['header']

    # SpotIQ analysis is just a Pinboard with property 'isAutocreated': True. 'isAutoDelete': true initially, but
    # switches if you have saved. This may change in the future
    def list_spotiqs(self, unsaved_only: bool = False, sort: str = 'DEFAULT', sort_ascending: bool = True,
                      filter: Optional[str] = None):
        full_listing = self.rest.metadata_listobjectheaders(object_type=MetadataNames.PINBOARD,
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
        self.rest.security_share(shared_object_type=MetadataNames.PINBOARD,
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


class AnswerMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_answers(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                    filter: Optional[str] = None, tags_filter: Optional[List[str]] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.ANSWER,
                                                    sort=sort,
                                                    sort_ascending=sort_ascending,
                                                    filter=filter,
                                                    tagname=tags_filter)



    def share_answers(self, shared_answer_guids: List[str], permissions: Dict,
                       notify_users: Optional[bool] = False, message: Optional[str] = None,
                       email_shares: List[str] = [], use_custom_embed_urls: bool = False):
        self.rest.security_share(shared_object_type=MetadataNames.ANSWER,
                                 shared_object_guids=shared_answer_guids,
                                 permissions=permissions,
                                 notify_users=notify_users,
                                 message=message,
                                 email_shares=email_shares,
                                 use_custom_embed_urls=use_custom_embed_urls)


class WorksheetMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_worksheets(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                       filter: Optional[str] = None, tags_filter: Optional[List[str]] = None):
        #  'subtypes': 'WORKSHEET'}
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.WORKSHEEET,
                                                    subtypes=[MetadataSubtypes.WORKSHEET],
                                                    sort=sort,
                                                    sort_ascending=sort_ascending,
                                                    filter=filter,
                                                    tagname=tags_filter)

    # Can Worksheets have the same name? May need more strict logic to check
    def find_guid(self, name: str) -> str:
        worksheets = self.list_worksheets(filter=name)
        # Filter is case-insensitive and the equivalent of a wild-card, so need to look for exact match
        # on the response
        for w in worksheets:
            if w['name'] == name:
                return w['id']
        raise LookupError()

    def assign_tags(self, worksheet_guids: List[str], tag_guids: List[str]):
        obj_type = MetadataNames.WORKSHEEET
        # The API requires a List with the content for each item
        obj_type_list = []
        for t in worksheet_guids:
            obj_type_list.append(obj_type)

        response = self.rest.metadata_assigntag(object_guids=worksheet_guids, object_type=obj_type_list,
                                                tag_guids=tag_guids)
        return response

    def share_worksheets(self, shared_worksheet_guids: List[str], permissions: Dict,
                       notify_users: Optional[bool] = False, message: Optional[str] = None,
                       email_shares: List[str] = [], use_custom_embed_urls: bool = False):
        self.rest.security_share(shared_object_type=MetadataNames.WORKSHEEET,
                                 shared_object_guids=shared_worksheet_guids,
                                 permissions=permissions,
                                 notify_users=notify_users,
                                 message=message,
                                 email_shares=email_shares,
                                 use_custom_embed_urls=use_custom_embed_urls)


class ConnectionMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_connections(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                        filter: Optional[str] = None, tags_filter: Optional[List[str]] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.CONNECTION,
                                                    sort=sort,
                                                    sort_ascending=sort_ascending,
                                                    filter=filter,
                                                    tagname=tags_filter)

    def connection_details(self, connection_guid):
        details = self.rest.metadata_details(object_type=MetadataNames.CONNECTION, object_guids=[connection_guid,])
        return details

    def find_guid(self, name: str) -> str:
        connections = self.list_connections(filter=name)
        # Filter is case-insensitive and the equivalent of a wild-card, so need to look for exact match
        # on the response
        for c in connections:
            if c['name'] == name:
                return c['id']
        raise LookupError()


class TableMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_tables(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                        filter: Optional[str] = None, tags_filter: Optional[List[str]] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.TABLE,
                                                    subtypes=[MetadataSubtypes.TABLE],
                                                    sort=sort,
                                                    sort_ascending=sort_ascending,
                                                    filter=filter,
                                                    tagname=tags_filter)

    def list_tables_for_connection(self, connection_guid: str, tags_filter: Optional[List[str]] = None) -> List:
        tables = self.list_tables(tags_filter=tags_filter)
        tables_for_conn = []
        for a in tables:
            if 'databaseStripe' in a:
                #print(a['databaseStripe'])
                if a['databaseStripe'] == connection_guid:
                    tables_for_conn.append(a)
        return tables_for_conn

    def find_guid(self, name: str, connection_guid: Optional[str] = None):
        tables = self.list_tables(filter=name)
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

    def assign_tags(self, table_guids: List[str], tag_guids: List[str]):
        obj_type = MetadataNames.TABLE
        # The API requires a List with the content for each item
        obj_type_list = []
        for t in table_guids:
            obj_type_list.append(obj_type)

        response = self.rest.metadata_assigntag(object_guids=table_guids, object_type=obj_type_list, tag_guids=tag_guids)
        return response


class TagMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_tags(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                  filter: Optional[str] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.TAG,
                                                    sort=sort,
                                                    sort_ascending=sort_ascending,
                                                    filter=filter)