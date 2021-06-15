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

class TSRest:
    def __init__(self, server: str):
        self.server = server
        self.session = requests.Session()
        # X-Requested-By is necessary for all calls. Accept: application/json
        # isn't necessary with requests which defaults to Accept: */* but might be in other frameworks
        # This sets the header on any subsequent call
        self.api_headers = {'X-Requested-By': 'ThoughtSpot', 'Accept': 'application/json'}
        self.api_headers= {'X-Requested-By': 'ThoughtSpot'}
        self.session.headers.update(self.api_headers)

    def build_url(self, ending: str, url_parameters: Optional[Dict] = None):
        base_url = '{}/callosum/v1/tspublic/v1/'.format(self.server)
        if url_parameters is not None:
            return "{}{}?{}".format(base_url, ending, parse.urlencode(url_parameters))
        else:
            return "{}{}".format(base_url, ending)

    def login(self, username: str, password: str):
        url = self.build_url("session/login")
        post_data = {'username': username, 'password': password, 'rememberme': 'true'}
        # Handle for errors
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()

    def logout(self):
        url = self.build_url("session/logout")
        # handle for errors
        response = self.session.post(url=url)

    # Basic Implementations
    def get_from_endpoint(self, endpoint: str, url_parameters: Optional[Dict] = None):
        url = self.build_url(ending=endpoint, url_parameters=url_parameters)
        response = self.session.get(url=url)
        response.raise_for_status()
        #print("Response headers:")
        #print(response.headers)
        return response.json()

    def post_to_endpoint(self, endpoint: str, post_data: Optional[Dict] = None, url_parameters: Optional[Dict] = None):
        url = self.build_url(endpoint, url_parameters=url_parameters)
        response = self.session.post(url=url, data=post_data)
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
        url = self.build_url(endpoint, url_parameters=url_parameters)

        response = self.session.post(url=url, files=post_data, headers={'Accept': "application/octet-stream"})
        response.raise_for_status()
        # print(response.request.headers)
        if len(response.content) == 0:
            return None
        else:
            return response.content

    def post_multipart(self, endpoint: str, post_data: Optional[Dict] = None, url_parameters: Optional[Dict] = None,
                       files: Optional[Dict] = None):
        url = self.build_url(endpoint, url_parameters=url_parameters)
        response = self.session.post(url=url, data=post_data, files=files)
        response.raise_for_status()
        if len(response.content) == 0:
            return None
        else:
            return response.json()

    def post_to_tml_endpoint(self, endpoint: str, post_data: Dict):
        url = self.build_url(endpoint)
        response = self.session.post(url=url, data=post_data, headers={'Accept': 'text/plain'})
        response.raise_for_status()
        print(response.content)
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

    # Auth Token
    def get_auth_token(self, secret_key: str, username: str, access_level: str, object_id: str):
        post_params = { 'secret_key': secret_key, 'username': username, 'access_level': access_level,
                        'id': object_id}
        response = self.post_to_endpoint("session/auth/token", post_data=post_params)

    # TML Specific Methods

    def export_tml(self, guid: str, formattype='JSON') -> Dict:
        # allow JSON or YAML in any casing
        formattype = formattype.upper()
        tml_post_params = {'export_ids': json.dumps([guid]),
                           'formattype': formattype,
                           'export_associated': 'false'}

        tml_response = self.post_to_tml_endpoint(endpoint="metadata/tml/export", post_data=tml_post_params)
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

    def export_tml_string(self, guid: str, formattype='JSON') -> str:
        # allow JSON or YAML in any casing
        formattype = formattype.upper()
        tml_post_params = {'export_ids': json.dumps([guid]),
                           'formattype': formattype,
                           'export_associated': 'false'}

        tml_response = self.post_to_tml_endpoint(endpoint="metadata/tml/export", post_data=tml_post_params)
        print(tml_response)
        objs = tml_response['object']

        if len(objs) == 1:
            yaml_str = objs[0]["edoc"]
            return yaml_str
        # This would only happen if you did 'export_associated': 'true' or got no response (would probably
        # throw some sort of HTTP exception
        else:
            raise Exception()

    def import_tml(self, tml, create_new_on_server=False, validate_only=False, formattype='JSON'):
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

        import_response = self.post_to_tml_endpoint(endpoint="metadata/tml/import", post_data=tml_post_params)
        return import_response.json()

    # Specific METADATA gets

    def get_pinboards(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                      filter: Optional[str] = None):
        params = {'type': MetadataNames.PINBOARD, 'sort': sort.upper(),
                  'sortascending': str(sort_ascending).lower()}
        if filter is not None:
            params['pattern'] = filter
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    # SpotIQ analysis is just a Pinboard with property 'isAutocreated': True. 'isAutoDelete': true initially, but
    # switches if you have saved. This may change in the future
    def get_spotiqs(self, unsaved_only: bool = False, sort: str = 'DEFAULT', sort_ascending: bool = True,
                      filter: Optional[str] = None):

        params = {'type': MetadataNames.PINBOARD, 'sort': sort.upper(),
                  'sortascending': str(sort_ascending).lower()}
        if filter is not None:
            params['pattern'] = filter

        full_listing = self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)
        final_list = []
        for pb in full_listing:
            if pb['isAutoCreated'] is True:
                if unsaved_only is True:
                    if pb["isAutoDelete"] is True:
                        final_list.append(pb)
                else:
                    final_list.append(pb)

        return final_list

    def get_pinboard(self, pb_id):
        # fetchids is JSON array of strings
        # skipids is JSON array of strings
        params = {'type': MetadataNames.PINBOARD, 'fetchids': '["{}"]'.format(pb_id)}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_answers(self, sort: str = 'DEFAULT', sort_ascending: bool = True,
                      filter: Optional[str] = None):
        params = {'type': MetadataNames.ANSWER, 'sort': sort.upper(),
                  'sortascending': str(sort_ascending).lower()}
        if filter is not None:
            params['pattern'] = filter
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    # Worksheets and Tables - how to distinguish
    def get_logical_tables(self):
        params = {'type': 'LOGICAL_TABLE'}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_worksheets(self):
        params = {'type': MetadataNames.WORKSHEEET}   #, 'subtypes': 'WORKSHEET'}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_connections(self):
        params = {'type': MetadataNames.CONNECTION}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    # Users

    def get_users(self):
        params = {'type': MetadataNames.USER}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_groups(self):
        params = {'type': MetadataNames.GROUP}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_all_users_and_groups(self):
        return self.get_from_endpoint('user/list')

    def transfer_ownership_of_objects_between_users(self, current_owner_username, new_owner_username):
        url_params = {'fromUserName': current_owner_username, 'toUserName': new_owner_username}
        return self.post_to_endpoint("user/transfer/ownership", url_parameters=url_params)

    # Data Methods
    def get_pinboard_data(self):
        pass

    # Export Options
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

    # Is password optional?
    def user_sync(self, principals_file, password: str, apply_changes=False, remove_deleted=False):
        files = {'principals': ('principals.json', principals_file, 'application/json'),
                 'applyChanges': str(apply_changes).lower(),
                 'removeDelete': str(remove_deleted).lower(),
                 'password': password}
        response = self.post_multipart('user/sync', post_data=None, files=files)
        return response

    def set_sharing(self, shared_object_type: str, shared_object_guids: List[str], permissions: Dict,
                    notify_users: Optional[bool] = False, message: Optional[str] = None ):
        params = {'type': shared_object_type, 'id': json.dumps(shared_object_guids),
                  'permission': json.dumps(permissions),
                  'notify': str(notify_users).lower(), 'emailshares': json.dumps([]),
                  'useCustomEmbedUrls': str(False).lower()
                  }
        if message is not None:
            params['message'] = message
        return self.post_to_endpoint("security/share", post_data=params)

    @staticmethod
    def get_sharing_permissions_dict():
        sharing_dict = {"permissions": {}}
        return sharing_dict

    @staticmethod
    def add_permission_to_dict(permissions_dict, guid, share_mode):
        for l1 in permissions_dict:
            permissions_dict[l1][guid] = {"shareMode": share_mode}
        return permissions_dict
