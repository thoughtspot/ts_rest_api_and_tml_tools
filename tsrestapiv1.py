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
    TABLE = 'LOGICAL_TABLE'


class ShareModes:
    READ_ONLY = 'READ_ONLY'
    FULL = 'FULL'
    NO_ACCESS = 'NO_ACCESS'


class Privileges:
    DATADOWNLOADING = 'DATADOWNLOADING'
    USERDATAUPLOADING = 'USERDATAUPLOADING'


# TSRestV1 is a full implementation of the ThoughtSpot Cloud REST APIs with the goal of
# making clear what is necessary for each API call.
#
# It is intentionally written with less abstraction than possible
# so that each REST API call can be viewed and understood as a 'reference implementation'.
# Yes, we could do it better / more Pythonically
# We have chosen to make it as simple to understand as possible

# The main TSRestV1 class implements all of the baseline API methods
# while the internal classes for individual object types (.user, .group, etc.) define specific use cases
# of the overall API footprint (for example, there are specific calls for Pinboards and Worksheets
# that call to the single metadata/listobjectheaders endpoint with the appropriate parameters)
class TSRestApiV1:
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

        # The documentation shows the /tspublic/v1/ portion but it is always preceded by {server}/callosum/v1/
        self.base_url = '{}/callosum/v1/tspublic/v1/'.format(self.server)

    #
    # Session management calls (up here vs. in the SESSION section below, because they are required)
    #
    def session_login(self, username: str, password: str) -> bool:
        endpoint = "session/login"
        post_data = {'username': username, 'password': password, 'rememberme': 'true'}

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()
        # Success is HTTP 204 with no content
        return True

    def session_logout(self) -> bool:
        endpoint = "session/logout"

        url = self.base_url + endpoint
        response = self.session.post(url=url)
        response.raise_for_status()

        # Success is HTTP 204 with no content
        return True

    #
    # root level API methods: Data Methods
    #
    def pinboarddata(self, pinboard_guid: str, vizids: List[str], format_type: str = 'COMPACT',
                     batch_size: int = -1, page_number: int = -1, offset: int = -1) -> Dict:
        endpoint = 'pinboarddata'
        post_data = {'id': pinboard_guid,
                     'vizid': json.dumps(vizids),
                     'batchsize': str(batch_size),
                     'pagenumber': str(page_number),
                     'offset': str(offset),
                     'formattype': format_type
                     }

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

    def searchdata(self, query_string: str, data_source_guid: str, format_type: str = 'COMPACT',
                     batch_size: int = -1, page_number: int = -1, offset: int = -1) -> Dict:
        endpoint = 'searchdata'
        post_data = {'query_string': query_string,
                     'data_source_guid': data_source_guid,
                     'batchsize': str(batch_size),
                     'pagenumber': str(page_number),
                     'offset': str(offset),
                     'formattype': format_type
                     }

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

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
                            visualization_ids: List[str] = None) -> bytes:
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

        url = self.base_url + endpoint
        # Requires Accept: application/octet-stream, return the content as binary bytes
        response = self.session.post(url=url, params=url_params, headers={'Accept': "application/octet-stream"})
        # Bytes format type, other methods can do what they want with it
        return response.content

    #
    # GROUP Methods
    #

    # Requires multipart/form-data
    def group_removeprivilege(self, privilege: str, group_names: List[str]):
        endpoint = 'group/removeprivilege'
        files = {'privilege': privilege,
                 'groupNames': json.dumps(group_names)
                }

        url = self.base_url + endpoint
        # Requires multipart/form-data
        response = self.session.post(url=url, files=files)
        response.raise_for_status()

        return response.json()

    # Requires multipart/form-data
    def group_addprivilege(self, privilege: str, group_names: str):
        endpoint = 'group/addprivilege'
        files = {'privilege': privilege,
                 'groupNames': json.dumps(group_names)
                }

        url = self.base_url + endpoint
        # Requires multipart/form-data
        response = self.session.post(url=url, files=files)
        response.raise_for_status()

        return response.json()

    #
    # MATERIALIZATION Methods
    #
    def materialization_refreshview(self, guid: str):
        endpoint = 'materialization/refreshview/{}'.format(guid)

        url = self.base_url + endpoint
        response = self.session.post(url=url)
        response.raise_for_status()

        return response.json()

    #
    # METADATA Methods
    #
    def metadata_details(self, object_type: str, object_guids: List[str], show_hidden: bool = False,
                         drop_question_details: bool = False) -> Dict:
        endpoint = 'metadata/details'
        url_params = {'type': object_type,
                      'id': json.dumps(object_guids),
                      'showhidden': str(show_hidden).lower(),
                      'dropquestiondetails': str(drop_question_details).lower()
                      }

        url = self.base_url + endpoint
        response = self.session.get(url=url, params=url_params)
        response.raise_for_status()

        return response.json()

    # Tag Methods
    def metadata_assigntag(self, object_guids: List[str], object_type: str, tag_guids: List[str]):
        endpoint = "metadata/assigntag"
        post_data = {'id': json.dumps(object_guids),
                     'type': object_type,
                     'tagid': json.dumps(tag_guids)
                     }

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

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

        url = self.base_url + endpoint
        response = self.session.get(url=url, params=url_params)
        response.raise_for_status()

        return response.json()

    def metadata_listvizheaders(self, guid: str) -> Dict:
        endpoint = "metadata/listvizheaders"
        url_params = {'id': guid}

        url = self.base_url + endpoint
        response = self.session.get(url=url, params=url_params)
        response.raise_for_status()

        return response.json()

    # metadata/listas is used to return the set of objects a user or group can access
    def metadata_listas(self, user_or_group_guid: str, user_or_group: str, minimum_access_level: str = 'READ_ONLY',
                        filter: Optional[str] = None) -> Dict:
        endpoint = "metadata/listas"
        url_params = {'type': user_or_group,
                      'principalid': user_or_group_guid,
                      'minimumaccesslevel': minimum_access_level,
                      }
        if filter is not None:
            url_params['pattern'] = filter

        url = self.base_url + endpoint
        response = self.session.get(url=url, params=url_params)
        response.raise_for_status()

        return response.json()

    # Favorite Methods
    def metadata_markasfavoritefor(self, user_guid: str, object_guids: List[str], object_type: str):
        endpoint = "metadata/markunmarkfavoritefor"
        post_data = {'type': object_type,
                     'ids': json.dumps(object_guids),
                     'userid': user_guid
                     }
        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

    def metadata_unmarkasfavoritefor(self, user_guid: str, object_guids: List[str]) -> bool:
        endpoint = "metadata/markunmarkfavoritefor"
        post_data = {'ids': json.dumps(object_guids),
                     'userid': user_guid
                     }

        url = self.base_url + endpoint
        response = self.session.delete(url=url, data=post_data)
        response.raise_for_status()

        return True
    #
    # TML Methods (METADATA/TML)
    # TML import and export are distinguished by using POST with an {'Accept': 'text/plain'} header on the POST
    #

    # Some errors come through as part of a HTTP 200 response, just listed in the JSON
    @staticmethod
    def raise_tml_errors(response):
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

    def metadata_tml_export(self, guid: str, formattype='JSON') -> Dict:
        endpoint = "metadata/tml/export"
        # allow JSON or YAML in any casing
        formattype = formattype.upper()
        post_data = {'export_ids': json.dumps([guid]),
                     'formattype': formattype,
                     'export_associated': 'false'
                     }

        url = self.base_url + endpoint
        # TML import is distinguished by having an {'Accept': 'text/plain'} header on the POST
        response = self.session.post(url=url, data=post_data, headers={'Accept': 'text/plain'})
        response.raise_for_status()
        # Extra parsing of some "error responses" that come through in JSON response on HTTP 200
        self.raise_tml_errors(response=response)

        # TML API returns a JSON response, with the TML document
        tml_json_response = response.json()
        objs = tml_json_response['object']

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
        post_data = {'export_ids': json.dumps([guid]),
                     'formattype': formattype,
                     'export_associated': 'false'
                     }
        url = self.base_url + endpoint

        # TML import is distinguished by having an {'Accept': 'text/plain'} header on the POST
        response = self.session.post(url=url, data=post_data, headers={'Accept': 'text/plain'})
        response.raise_for_status()
        # Extra parsing of some "error responses" that come through in JSON response on HTTP 200
        self.raise_tml_errors(response=response)

        # TML API returns a JSON response, with the TML document
        tml_json_response = response.json()
        objs = tml_json_response['object']

        if len(objs) == 1:
            yaml_str = objs[0]["edoc"]
            return yaml_str
        # This would only happen if you did 'export_associated': 'true' or got no response (would probably
        # throw some sort of HTTP exception
        else:
            raise Exception()

    # TML import is distinguished by having an {'Accept': 'text/plain'} header on the POST
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

        post_data = {"import_objects": json_encoded_tml,
                     "import_policy": import_policy,
                     "force_create": str(create_new_on_server).lower()
                     }

        url = self.base_url + endpoint

        # TML import is distinguished by having an {'Accept': 'text/plain'} header on the POST
        response = self.session.post(url=url, data=post_data, headers={'Accept': 'text/plain'})
        response.raise_for_status()
        # Extra parsing of some "error responses" that come through in JSON response on HTTP 200
        self.raise_tml_errors(response=response)
        return response.json()

    #
    # PARTNER methods
    #
    def partner_snowflake_user(self, body: Dict):
        endpoint = 'partner/snowflake/user'
        post_data = {'body': json.dumps(body)}

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

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
    def security_share(self, shared_object_type: str,
                       shared_object_guids: List[str],
                       permissions: Dict,
                       notify_users: Optional[bool] = False,
                       message: Optional[str] = None,
                       email_shares: List[str] = [],
                       use_custom_embed_urls: bool = False
                       ):
        endpoint = "security/share"
        post_data = {'type': shared_object_type,
                     'id': json.dumps(shared_object_guids),
                     'permission': json.dumps(permissions),
                     'notify': str(notify_users).lower(),
                     'emailshares': json.dumps(email_shares),
                     'useCustomEmbedUrls': str(use_custom_embed_urls).lower()
                     }
        if message is not None:
            post_data['message'] = message

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

    # Shares just a single viz within a Pinboard, without more complex sharing permissions of security/share
    def security_shareviz(self,
                          shared_object_type: str,
                          pinboard_guid: str,
                          viz_guid: str,
                          principal_ids: List[str],
                          notify_users: Optional[bool] = False,
                          message: Optional[str] = None,
                          email_shares: List[str] = [],
                          use_custom_embed_urls: bool = False
                          ):
        endpoint = "security/shareviz"
        post_data = {'type': shared_object_type,
                  'pinboardId': pinboard_guid,
                  'principalids': json.dumps(principal_ids),
                  'vizid': viz_guid,
                  'notify': str(notify_users).lower(),
                  'emailshares': json.dumps(email_shares),
                  'useCustomEmbedUrls': str(use_custom_embed_urls).lower()
                  }
        if message is not None:
            post_data['message'] = message

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

    #
    # SESSION Methods
    #

    # Home Pinboard Methods
    def session_homepinboard_set(self, pinboard_guid: str, user_guid: str):
        endpoint = 'session/homepinboard'
        post_data = {'id': pinboard_guid,
                     'userid': user_guid
                     }

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

    def session_homepinboard_get(self):
        endpoint = 'session/homepinboard'

        url = self.base_url + endpoint
        response = self.session.get(url=url)
        response.raise_for_status()

        return response.json()

    def session_homepinboard_delete(self) -> bool:
        endpoint = 'session/homepinboard'

        url = self.base_url + endpoint
        response = self.session.delete(url=url)
        response.raise_for_status()

        return True

    def session_group_listuser(self, group_guid: str):
        endpoint = "session/group/listuser/{}".format(group_guid)
        url_params = {"groupid": group_guid}

        url = self.base_url + endpoint
        response = self.session.get(url=url, params=url_params)
        response.raise_for_status()

        return response.json()

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

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

    # Implementation of the user/sync endpoint, which is fairly complex and runs a risk with the remove_deleted option
    # set to true
    # Uses a multi-part POST, with the type of the principals parameter set to application/json
    def user_sync(self, principals_file, password: str, apply_changes=False, remove_deleted=False):
        endpoint = 'user/sync'
        # You must set the type of principals to 'application/json' or 'text/json'
        files = {'principals': ('principals.json', principals_file, 'application/json'),
                 'applyChanges': str(apply_changes).lower(),
                 'removeDeleted': str(remove_deleted).lower(),
                 'password': password
                 }

        url = self.base_url + endpoint
        response = self.session.post(url=url, data=None, files=files)
        response.raise_for_status()

        return response.json()

    def user_transfer_ownership(self, current_owner_username, new_owner_username):
        endpoint = "user/transfer/ownership"
        url_params = {'fromUserName': current_owner_username,
                      'toUserName': new_owner_username
                      }
        url = self.base_url + endpoint
        response = self.session.post(url=url, params=url_params)
        response.raise_for_status()

        return response.json()

    # Preferences and preferencesProto are a big ?
    def user_updatepreference(self, user_guid: str, username: str, preferences: Dict, preferencesProto: str):
        endpoint = 'user/updatepreference'
        post_data = {'userid': user_guid,
                     'username': username,
                     'preferences': json.dumps(preferences),
                     'preferencesProto': preferencesProto
                     }
        url = self.base_url + endpoint
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

        return response.json()

    # Retrieves all USER and USER_GROUP objects
    def user_list(self):
        endpoint = 'user/list'

        url = self.base_url + endpoint
        response = self.session.get(url=url)
        response.raise_for_status()

        return response.json()



