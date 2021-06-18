from tsrestapiv1 import *

#
# Each of these classes is used as an object within the main wrapper class
# to provide a structure based on the object types available within ThoughtSpot
# Any given class may call to various APIs to accomplish the goal specific to that object type
#

class TMLMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def export_tml(self, guid: str, formattype='JSON'):
        return self.rest.metadata_tml_export(guid=guid, formattype=formattype)

    # Synonym for export
    def download(self, guid: str, formattype='JSON'):
        return self.rest.metadata_tml_export(guid=guid, formattype=formattype)

    def import_tml(self):
        pass

    # Synonym for import
    def upload_tml(self):
        pass

    def publish_new(self):
        pass


class UserMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_users(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                   filter: Optional[str] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.USER, sort=sort,
                                                    sort_ascending=sort_ascending, filter=filter)

    def list_available_objects_for_user(self, user_guid: str, minimum_access_level: str = 'READ_ONLY',
                                        filter: Optional[str] = None):
        return self.rest.metadata_listas(user_or_group_guid=user_guid, user_or_group=MetadataNames.USER,
                                         minimum_access_level=minimum_access_level,filter=filter)

    def privileges_for_user(self, user_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.USER, object_guids=[user_guid, ])
        return details["storables"][0]['privileges']

    def assigned_groups_for_user(self, user_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.USER, object_guids=[user_guid, ])
        return details["storables"][0]['assignedGroups']

    def inherited_groups_for_user(self, user_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.USER, object_guids=[user_guid, ])
        return details["storables"][0]['inheritedGroups']

    # Used when a user should be removed from the system but their content needs to be reassigned to a new owner
    def transfer_ownership_of_objects_between_users(self, current_owner_username, new_owner_username):
        return self.rest.user_transfer_ownership(current_owner_username=current_owner_username,
                                                 new_owner_username=new_owner_username)


class GroupMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_groups(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                        filter: Optional[str] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.GROUP, sort=sort,
                                               sort_ascending=sort_ascending, filter=filter)

    # This endpoint is under session/ as the root which makes it hard to find in the listings
    def list_users_in_group(self, group_guid: str):
        return self.rest.session_group_listuser(group_guid=group_guid)

    def list_available_objects_for_group(self, group_guid: str, minimum_access_level: str = 'READ_ONLY',
                                        filter: Optional[str] = None):
        return self.rest.metadata_listas(user_or_group_guid=group_guid, user_or_group=MetadataNames.GROUP,
                                         minimum_access_level=minimum_access_level,filter=filter)

    def privileges_for_group(self, group_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.GROUP, object_guids=[group_guid, ])
        return details["storables"][0]['privileges']

    # Does this even make sense?
    def assigned_groups_for_group(self, group_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.GROUP, object_guids=[group_guid, ])
        return details["storables"][0]['assignedGroups']

    def inherited_groups_for_group(self, group_guid: str):
        details = self.rest.metadata_details(object_type=MetadataNames.GROUP, object_guids=[group_guid, ])
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
        return self.rest.group_removeprivilege(privilege=privilege, group_names=group_name)


class PinboardMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_pinboards(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                      filter: Optional[str] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.PINBOARD, sort=sort,
                                               sort_ascending=sort_ascending, filter=filter)

    def get_pinboard_by_id(self, pb_id):
        endpoint = "metadata/listobjectheaders"
        # fetchids is JSON array of strings, we are building manually for singular here
        # skipids is JSON array of strings
        url_params = {'type': MetadataNames.PINBOARD,
                      'fetchids': '["{}"]'.format(pb_id)
                      }
        return self.rest.get_from_endpoint(endpoint=endpoint, url_parameters=url_params)

    # SpotIQ analysis is just a Pinboard with property 'isAutocreated': True. 'isAutoDelete': true initially, but
    # switches if you have saved. This may change in the future
    def list_spotiqs(self, unsaved_only: bool = False, sort: str = 'DEFAULT', sort_ascending: bool = True,
                      filter: Optional[str] = None):
        full_listing = self.rest.metadata_listobjectheaders(object_type=MetadataNames.PINBOARD, sort=sort,
                                                            sort_ascending=sort_ascending, filter=filter)
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
                       email_shares: List[str] = [], use_custom_embed_urls: bool = False):
        self.rest.security_share(shared_object_type=MetadataNames.PINBOARD, shared_object_guids=shared_pinboard_guids,
                                 permissions=permissions, notify_users=notify_users, message=message,
                                 email_shares=email_shares, use_custom_embed_urls=use_custom_embed_urls)

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
                    filter: Optional[str] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.ANSWER, sort=sort,
                                                    sort_ascending=sort_ascending, filter=filter)

    def share_answers(self, shared_answer_guids: List[str], permissions: Dict,
                       notify_users: Optional[bool] = False, message: Optional[str] = None,
                       email_shares: List[str] = [], use_custom_embed_urls: bool = False):
        self.rest.security_share(shared_object_type=MetadataNames.ANSWER, shared_object_guids=shared_answer_guids,
                                 permissions=permissions, notify_users=notify_users, message=message,
                                 email_shares=email_shares, use_custom_embed_urls=use_custom_embed_urls)


class WorksheetMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_worksheets(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                       filter: Optional[str] = None):
        #  'subtypes': 'WORKSHEET'}
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.WORKSHEEET, sort=sort,
                                                    sort_ascending=sort_ascending, filter=filter)

    def share_worksheets(self, shared_worksheet_guids: List[str], permissions: Dict,
                       notify_users: Optional[bool] = False, message: Optional[str] = None,
                       email_shares: List[str] = [], use_custom_embed_urls: bool = False):
        self.rest.security_share(shared_object_type=MetadataNames.WORKSHEEET, shared_object_guids=shared_worksheet_guids,
                                 permissions=permissions, notify_users=notify_users, message=message,
                                 email_shares=email_shares, use_custom_embed_urls=use_custom_embed_urls)


class ConnectionMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_connections(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                        filter: Optional[str] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.CONNECTION, sort=sort,
                                               sort_ascending=sort_ascending, filter=filter)


class TableMethods:
    def __init__(self, tsrest: TSRestApiV1):
        self.rest = tsrest

    def list_tables(self):
        endpoint = "metadata/listobjectheaders"
        url_params = {'type': 'LOGICAL_TABLE'}
        return self.rest.get_from_endpoint(endpoint=endpoint, url_parameters=url_params)