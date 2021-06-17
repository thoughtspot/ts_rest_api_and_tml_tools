import requests
from typing import Optional, Dict, List
from urllib import parse
import json
import yaml


class MetadataNames:
    USER = 'USER'
    GROUP = 'USER_GROUP'
    PINBOARD = 'PINBOARD_ANSWER_BOOK'
    WORKSHEEET = 'LOGICAL_TABLE'
    CONNECTION = 'DATA_SOURCE'
    ANSWER = 'QUESTION_ANSWER_BOOK'


class ShareModes:
    READ_ONLY = 'READ_ONLY'
    FULL = 'FULL'
    NO_ACCESS = 'NO_ACCESS'


class Privileges:
    DATADOWNLOADING = 'DATADOWNLOADING'
    USERDATAUPLOADING = 'USERDATAUPLOADING'



# TSRestV1 is a simple implementation of the ThoughtSpot Cloud REST APIs
# The main TSRestV1 class implements all of the baseline API methods
# while the internal classes for individual object types (.user, .group, etc.) define specific use cases
# of the overall API footprint (for example, there are specific calls for Pinboards and Worksheets
# that call to the single metadata/listobjectheaders endpoint with the appropriate parameters)
class TSRestV1:
    def __init__(self, server_url: str):
        # Protect from extra end slash on URL
        if server_url[-1] == "/":
            server_url = server_url[0:-1]
        self.server = server_url

        # REST API uses cookies to maintain the session, so you need to create an open Session
        self.session = requests.Session()

        # X-Requested-By is necessary for all calls. Accept: application/json
        # isn't necessary with requests which defaults to Accept: */* but might be in other frameworks
        # This sets the header on any subsequent call
        self.api_headers = {'X-Requested-By': 'ThoughtSpot', 'Accept': 'application/json'}
        # self.api_headers= {'X-Requested-By': 'ThoughtSpot'}
        self.session.headers.update(self.api_headers)

    # Helper method to build out the full URL from just the endpoint ending from the documentation
    def build_endpoint_url(self, ending: str, url_parameters: Optional[Dict] = None):
        base_url = '{}/callosum/v1/tspublic/v1/'.format(self.server)
        if url_parameters is not None:
            return "{}{}?{}".format(base_url, ending, parse.urlencode(url_parameters))
        else:
            return "{}{}".format(base_url, ending)

    #
    # Basic Implementations of the REST calls using requests library
    #
    def get_from_endpoint(self, endpoint: str, url_parameters: Optional[Dict] = None):
        url = self.build_endpoint_url(ending=endpoint, url_parameters=url_parameters)
        response = self.session.get(url=url)
        response.raise_for_status()
        return response.json()

    def post_to_endpoint(self, endpoint: str, post_data: Optional[Dict] = None, url_parameters: Optional[Dict] = None):
        url = self.build_endpoint_url(endpoint, url_parameters=url_parameters)
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()
        if len(response.content) == 0:
            return None
        else:
            return response.json()

    def del_from_endpoint(self, endpoint: str, post_data: Optional[Dict] = None, url_parameters: Optional[Dict] = None):
        url = self.build_endpoint_url(endpoint, url_parameters=url_parameters)
        response = self.session.delete(url=url, data=post_data)
        response.raise_for_status()
        if len(response.content) == 0:
            return None
        else:
            return response.json()

#    def get_from_endpoint_binary_response(self, endpoint: str, url_parameters: Optional[Dict] = None):
#        url = self.build_url(ending=endpoint, url_parameters=url_parameters)
#        response = self.session.get(url=url, headers={'Accept': "application/octet-stream"})
#        response.raise_for_status()
#        return response.content

    def post_to_endpoint_binary_response(self, endpoint: str, post_data: Optional[Dict] = None, url_parameters: Optional[Dict] = None):
        url = self.build_endpoint_url(endpoint, url_parameters=url_parameters)

        response = self.session.post(url=url, files=post_data, headers={'Accept': "application/octet-stream"})
        response.raise_for_status()
        # print(response.request.headers)
        if len(response.content) == 0:
            return None
        else:
            return response.content

    def post_multipart(self, endpoint: str, post_data: Optional[Dict] = None, url_parameters: Optional[Dict] = None,
                       files: Optional[Dict] = None):
        url = self.build_endpoint_url(endpoint, url_parameters=url_parameters)
        response = self.session.post(url=url, data=post_data, files=files)
        response.raise_for_status()
        if len(response.content) == 0:
            return None
        else:
            return response.json()

    def post_to_tml_endpoint(self, endpoint: str, post_data: Dict):
        url = self.build_endpoint_url(endpoint)
        response = self.session.post(url=url, data=post_data, headers={'Accept': 'text/plain'})
        response.raise_for_status()
        if len(response.content) == 0:
            print(response.status_code)
            raise Exception()
        else:
            j = response.json()
            # JSON error response checking
            if 'object' in j:
                for k in j['object']:
                    if 'info' in k:
                        if k['info']['status']['status_code'] == 'ERROR':
                            print(k['info']['status']['error_message'])
                            raise Exception()
                        else:
                            return response.json()
                    else:
                        return response.json()
            else:

                return response.json()

    #
    # Session management calls (up here vs. in the SESSION section below, because they are required)
    #
    def session_login(self, username: str, password: str):
        endpoint = "session/login"
        post_data = {'username': username, 'password': password, 'rememberme': 'true'}
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    def session_logout(self):
        endpoint = "session/logout"
        return self.post_to_endpoint(endpoint=endpoint)

    #
    # root level API methods: Data Methods
    #
    def pinboarddata(self, pinboard_guid: str, vizids: List[str], format_type: str = 'COMPACT',
                     batch_size: int = -1, page_number: int = -1, offset: int = -1):
        endpoint = 'pinboarddata'
        post_data = {'id': pinboard_guid,
                     'vizid': json.dumps(vizids),
                     'batchsize': str(batch_size),
                     'pagenumber': str(page_number),
                     'offset': str(offset),
                     'formattype': format_type
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    def searchdata(self, query_string: str, data_source_guid: str, format_type: str = 'COMPACT',
                     batch_size: int = -1, page_number: int = -1, offset: int = -1):
        endpoint = 'searchdata'
        post_data = {'query_string': query_string,
                     'data_source_guid': data_source_guid,
                     'batchsize': str(batch_size),
                     'pagenumber': str(page_number),
                     'offset': str(offset),
                     'formattype': format_type
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    #
    # DATABASE methods - only applicable to Software using Falcon (will implement later)
    #

    #
    # EXPORT Methods
    #
    def export_pinboard_pdf(self, pinboard_id: str,
                            one_visualization_per_page: bool = False,
                            landscape_or_portrait="LANDSCAPE",
                            cover_page: bool = True, logo: bool = True,
                            page_numbers: bool = False, filter_page: bool = True,
                            truncate_tables: bool = False,
                            footer_text: str = None,
                            visualization_ids: List[str] = None):
        endpoint = "export/pinboard/pdf"

        # There is a "transient_pinboard_content" option but it would only make sense within the browser

        # Unclear how to use visualization_ids, so not implemented yet

        layout_type = 'PINBOARD'
        if one_visualization_per_page is True:
            layout_type = 'VISUALIZATION'
        url_params = {"id": pinboard_id,
                      "layout_type": layout_type,
                      "orientation": landscape_or_portrait.upper(),
                      "truncate_tables": str(truncate_tables).lower(),
                      "include_cover_page": str(cover_page).lower(),
                      "include_logo": str(logo).lower(),
                      "include_page_number": str(page_numbers).lower(),
                      "include_filter_page": str(filter_page).lower(),
                      }
        if footer_text is not None:
            url_params["footer_text"] = footer_text
        return self.post_to_endpoint_binary_response(endpoint=endpoint, post_data=url_params)

    #
    # GROUP Methods
    #

    ##
    # ERRORS in implementation, pending a documentation update to correct
    ##
    def group_removeprivilege(self, privilege: str, group_names: str):
        endpoint = 'group/removeprivilege'
        post_data = {'privilege': privilege,
                     'groupNames': group_names
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    ##
    # ERRORS in implementation, pending a documentation update to correct
    ##
    def group_addprivilege(self, privilege: str, group_names: str):
        endpoint = 'group/addprivilege'
        post_data = {'privilege': privilege,
                     'groupNames': group_names
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    #
    # MATERIALIZATION Methods
    #
    def materialization_refreshview(self, guid: str):
        endpoint = 'materialization/refreshview/{}'.format(guid)
        return self.post_to_endpoint(endpoint=endpoint)

    #
    # METADATA Methods
    #
    def metadata_details(self, object_type: str, object_guids: List[str], show_hidden: bool = False,
                         drop_question_details: bool = False):
        endpoint = 'metadata/details'
        url_params = {'type': object_type,
                      'id': json.dumps(object_guids),
                      'showhidden': str(show_hidden).lower(),
                      'dropquestiondetails': str(drop_question_details).lower()
                      }
        return self.get_from_endpoint(endpoint=endpoint, url_parameters=url_params)

    # Tag Methods
    def metadata_assigntag(self, object_guids: List[str], object_type: str, tag_guids: List[str]):
        endpoint = "metadata/assigntag"
        post_data = {'id': json.dumps(object_guids),
                     'type': object_type,
                     'tagid': json.dumps(tag_guids)
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    def metadata_listobjectheaders(self, object_type: str, sort: str = 'DEFAULT', sort_ascending: bool = True,
                                   filter: Optional[str] = None, fetchids: Optional[str] = None,
                                   skipids: Optional[str] = None):
        endpoint = "metadata/listobjectheaders"
        url_params = {'type': object_type,
                      'sort': sort.upper(),
                      'sortascending': str(sort_ascending).lower()
                      }
        if filter is not None:
            url_params['pattern'] = filter
        return self.get_from_endpoint(endpoint=endpoint, url_parameters=url_params)

    def metadata_listvizheaders(self, guid:str):
        endpoint = "metadata/listvizheaders"
        url_params = {'id': guid}
        return self.get_from_endpoint(endpoint=endpoint, url_parameters=url_params)

    # metadata/listas is used to return the set of objects a user or group can access
    def metadata_listas(self, user_or_group_guid: str, user_or_group: str, minimum_access_level: str = 'READ_ONLY',
                        filter: Optional[str] = None):
        endpoint = "metadata/listas"
        url_params = {'type': user_or_group,
                      'principalid': user_or_group_guid,
                      'minimumaccesslevel': minimum_access_level,
                      }
        if filter is not None:
            url_params['pattern'] = filter
        return self.get_from_endpoint(endpoint=endpoint, url_parameters=url_params)

    # Favorite Methods
    def metadata_markasfavoritefor(self, user_guid: str, object_guids: List[str], object_type: str):
        endpoint = "metadata/markunmarkfavoritefor"
        post_data = {'type': object_type,
                     'ids': json.dumps(object_guids),
                     'userid': user_guid
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    def metadata_unmarkasfavoritefor(self, user_guid: str, object_guids: List[str]):
        endpoint = "metadata/markunmarkfavoritefor"
        post_data = {'ids': json.dumps(object_guids),
                     'userid': user_guid
                     }
        return self.del_from_endpoint(endpoint=endpoint, post_data=post_data)

    #
    # TML Methods (METADATA/TML)
    #
    def metadata_tml_export(self, guid: str, formattype='JSON') -> Dict:
        endpoint = "metadata/tml/export"
        # allow JSON or YAML in any casing
        formattype = formattype.upper()
        tml_post_params = {'export_ids': json.dumps([guid]),
                           'formattype': formattype,
                           'export_associated': 'false'}

        tml_response = self.post_to_tml_endpoint(endpoint=endpoint, post_data=tml_post_params)
        #print(tml_response)
        objs = tml_response['object']

        if len(objs) == 1:
            yaml_str = objs[0]["edoc"]
            if formattype == 'YAML':
                tml_obj = yaml.load(yaml_str, Loader=yaml.Loader)
            elif formattype == 'JSON':
                tml_obj = json.loads(yaml_str)
            else:
                raise Exception()
            return tml_obj
        # This would only happen if you did 'export_associated': 'true' or got no response (would probably
        # throw some sort of HTTP exception
        else:
            raise Exception()

    def metadata_tml_export_string(self, guid: str, formattype='JSON') -> str:
        endpoint = "metadata/tml/export"
        # allow JSON or YAML in any casing
        formattype = formattype.upper()
        tml_post_params = {'export_ids': json.dumps([guid]),
                           'formattype': formattype,
                           'export_associated': 'false'}

        tml_response = self.post_to_tml_endpoint(endpoint=endpoint, post_data=tml_post_params)
        print(tml_response)
        objs = tml_response['object']

        if len(objs) == 1:
            yaml_str = objs[0]["edoc"]
            return yaml_str
        # This would only happen if you did 'export_associated': 'true' or got no response (would probably
        # throw some sort of HTTP exception
        else:
            raise Exception()

    def metadata_tml_import(self, tml, create_new_on_server=False, validate_only=False, formattype='JSON'):
        endpoint = "metadata/tml/import"
        # allow JSON or YAML in any casing
        formattype = formattype.upper()

        if formattype == 'JSON':
            json_encoded_tml = json.dumps([tml])
        elif formattype == 'YAML':
            json_encoded_tml = json.dumps([tml])
        # Assume it's just a Python object which will dump to JSON matching the TML format
        else:
            json_encoded_tml = json.dumps([tml])
        import_policy = "ALL_OR_NONE"
        if validate_only is True:
            import_policy = 'VALIDATE_ONLY'
        tml_post_params = {"import_objects": json_encoded_tml,
                           "import_policy": import_policy,
                           "force_create": str(create_new_on_server).lower()}

        import_response = self.post_to_tml_endpoint(endpoint=endpoint, post_data=tml_post_params)
        return import_response.json()

    #
    # PARTNER methods
    #
    def partner_snowflake_user(self, body: Dict):
        endpoint = 'partner/snowflake/user'
        post_data = {'body': json.dumps(body)}
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    #
    # SECURITY methods
    #

    # Content in ThoughtSpot belongs to its author/owner
    # It can be shared to other Groups or Users

    # There is a particular JSON object structure for giving sharing permissions
    # This method gives you a blank permissions Dict for that purpose
    @staticmethod
    def get_sharing_permissions_dict():
        sharing_dict = {"permissions": {}}
        return sharing_dict

    # This method takes in an existing permissions Dict and adds a new entry to it
    # It returns back the permissions Dict but there is never a copy, it acts upon the Dict passed in
    @staticmethod
    def add_permission_to_dict(permissions_dict, guid, share_mode):
        for l1 in permissions_dict:
            permissions_dict[l1][guid] = {"shareMode": share_mode}
        return permissions_dict

    # Share any object type
    # Requires a Permissions Dict, which can be generated and modified with the two static methods above
    def security_share(self, shared_object_type: str, shared_object_guids: List[str], permissions: Dict,
                    notify_users: Optional[bool] = False, message: Optional[str] = None, email_shares: List[str] = [],
                    use_custom_embed_urls: bool = False):
        endpoint = "security/share"
        params = {'type': shared_object_type,
                  'id': json.dumps(shared_object_guids),
                  'permission': json.dumps(permissions),
                  'notify': str(notify_users).lower(),
                  'emailshares': json.dumps(email_shares),
                  'useCustomEmbedUrls': str(use_custom_embed_urls).lower()
                  }
        if message is not None:
            params['message'] = message
        return self.post_to_endpoint(endpoint=endpoint, post_data=params)

    # Shares just a single viz within a Pinboard, without more complex sharing permissions of security/share
    def security_shareviz(self, shared_object_type: str, pinboard_guid: str, viz_guid: str, principal_ids: List[str],
                    notify_users: Optional[bool] = False, message: Optional[str] = None, email_shares: List[str] = [],
                    use_custom_embed_urls: bool = False):
        endpoint = "security/shareviz"
        params = {'type': shared_object_type,
                  'pinboardId': pinboard_guid,
                  'principalids': json.dumps(principal_ids),
                  'vizid': viz_guid,
                  'notify': str(notify_users).lower(),
                  'emailshares': json.dumps(email_shares),
                  'useCustomEmbedUrls': str(use_custom_embed_urls).lower()
                  }
        if message is not None:
            params['message'] = message
        return self.post_to_endpoint(endpoint=endpoint, post_data=params)

    #
    # SESSION Methods
    #

    # Home Pinboard Methods
    def session_homepinboard_set(self, pinboard_guid: str, user_guid: str):
        endpoint = 'session/homepinboard'
        post_data = {'id': pinboard_guid,
                     'userid': user_guid
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    def session_homepinboard_get(self):
        endpoint = 'session/homepinboard'
        return self.get_from_endpoint(endpoint=endpoint)

    def session_homepinboard_delete(self):
        endpoint = 'session/homepinboard'
        return self.del_from_endpoint(endpoint=endpoint)

    def session_group_listuser(self, group_guid: str):
        endpoint = "session/group/listuser/{}".format(group_guid)
        url_params = {"groupid": group_guid}
        return self.get_from_endpoint(endpoint=endpoint, url_parameters=url_params)

    # session/login/token is not implemented here, it is intended for a browser login

    # The below shows an implementation of session/auth/token but it should only be used from Authenticator Server
    # with Secret Key retrieved in a secure manner only in memory
    #    def session_auth_token(self, secret_key: str, username: str, access_level: str, object_id: str):
    #        post_params = { 'secret_key': secret_key, 'username': username, 'access_level': access_level,
    #                        'id': object_id}
    #        response = self.post_to_endpoint("session/auth/token", post_data=post_params)
    #        return response

    #
    # USER Methods
    #
    def user_updatepassword(self, username: str, current_password: str, new_password: str):
        endpoint = 'user/updatepassword'
        post_data = {'name': username,
                     'currentpassword': current_password,
                     'newpassword': new_password
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    # Implementation of the user/sync endpoint, which is fairly complex and runs a risk with the remove_deleted option
    # set to true
    def user_sync(self, principals_file, password: str, apply_changes=False, remove_deleted=False):
        endpoint = 'user/sync'
        files = {'principals': ('principals.json', principals_file, 'application/json'),
                 'applyChanges': str(apply_changes).lower(),
                 'removeDelete': str(remove_deleted).lower(),
                 'password': password
                 }
        response = self.post_multipart(endpoint=endpoint, post_data=None, files=files)
        return response

    def user_transfer_ownership(self, current_owner_username, new_owner_username):
        endpoint = "user/transfer/ownership"
        url_params = {'fromUserName': current_owner_username,
                      'toUserName': new_owner_username
                      }
        return self.post_to_endpoint(endpoint=endpoint, url_parameters=url_params)

    # Preferences and preferencesProto are a big ?
    def user_updatepreference(self, user_guid: str, username: str, preferences: Dict, preferencesProto: str):
        endpoint = 'user/updatepreference'
        post_data = {'userid': user_guid,
                     'username': username,
                     'preferences': json.dumps(preferences),
                     'preferencesProto': preferencesProto
                     }
        return self.post_to_endpoint(endpoint=endpoint, post_data=post_data)

    # Retrieves all USER and USER_GROUP objects
    def user_list(self):
        endpoint = 'user/list'
        return self.get_from_endpoint(endpoint=endpoint)




#
# Method Helper classes, organized by Object Type
#
class TMLMethods:
    def __init__(self, tsrest: TSRestV1):
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
    def __init__(self, tsrest: TSRestV1):
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
    def __init__(self, tsrest: TSRestV1):
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


class PinboardMethods:
    def __init__(self, tsrest: TSRestV1):
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
    def __init__(self, tsrest: TSRestV1):
        self.rest = tsrest

    def list_answers(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                    filter: Optional[str] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.ANSWER, sort=sort,
                                                    sort_ascending=sort_ascending, filter=filter)


class WorksheetMethods:
    def __init__(self, tsrest: TSRestV1):
        self.rest = tsrest

    def list_worksheets(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                       filter: Optional[str] = None):
        #  'subtypes': 'WORKSHEET'}
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.WORKSHEEET, sort=sort,
                                               sort_ascending=sort_ascending, filter=filter)


class ConnectionMethods:
    def __init__(self, tsrest: TSRestV1):
        self.rest = tsrest

    def list_connections(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                        filter: Optional[str] = None):
        return self.rest.metadata_listobjectheaders(object_type=MetadataNames.CONNECTION, sort=sort,
                                               sort_ascending=sort_ascending, filter=filter)


class TableMethods:
    def __init__(self, tsrest: TSRestV1):
        self.rest = tsrest

    def list_tables(self):
        endpoint = "metadata/listobjectheaders"
        url_params = {'type': 'LOGICAL_TABLE'}
        return self.rest.get_from_endpoint(endpoint=endpoint, url_parameters=url_params)


#
# Wrapper to organize everything
#
class ThoughtSpotRest:
    def __init__(self, server_url: str):
        self.tsrest = TSRestV1(server_url=server_url)
        self.user = UserMethods(self.tsrest)
        self.group = GroupMethods(self.tsrest)
        self.tml = TMLMethods(self.tsrest)
        self.pinboard = PinboardMethods(self.tsrest)
        self.answer = AnswerMethods(self.tsrest)
        self.connection = ConnectionMethods(self.tsrest)
        self.worksheet = WorksheetMethods(self.tsrest)
        self.table = TableMethods(self.tsrest)

    def login(self, username: str, password: str):
        return self.tsrest.session_login(username=username, password=password)

    def logout(self):
        return self.tsrest.session_logout()

