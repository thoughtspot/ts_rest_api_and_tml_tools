import requests
from typing import Optional, Dict
from urllib import parse
import json
import yaml


class TSRest:
    def __init__(self, server: str):
        self.server = server
        self.session = requests.Session()
        # X-Requested-By is necessary for all calls. Accept: application/json
        # isn't necessary with requests which defaults to Accept: */* but might be in other frameworks
        # This sets the header on any subsequent call
        self.api_headers = {'X-Requested-By': 'ThoughtSpot', 'Accept': 'application/json'}
        # self.api_headers= {'X-Requested-By': 'ThoughtSpot'}
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
        return response.json()

    def post_to_endpoint(self, endpoint: str, post_data: Dict, url_parameters: Optional[Dict] = None):
        url = self.build_url(endpoint, url_parameters=url_parameters)
        response = self.session.post(url=url, data=post_data)
        response.raise_for_status()
        if len(response.content) == 0:
            return None
        else:
            return response.json()

    def post_to_tml_endpoint(self, endpoint: str, post_data: Dict):
        url = self.build_url(endpoint)
        response = self.session.post(url=url, data=post_data, headers={'Accept': 'text/plain'})
        response.raise_for_status()
        if len(response.content) == 0:
            return None
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
        #print(tml_response)
        objs = tml_response['object']

        if len(objs) == 1:
            yaml_str = objs[0]["edoc"]
            return yaml_str
        # This would only happen if you did 'export_associated': 'true' or got no response (would probably
        # throw some sort of HTTP exception
        else:
            raise Exception()

    def import_tml(self, tml_obj, create_new_on_server=False, validate_only=False, formattype='JSON'):
        # allow JSON or YAML in any casing
        formattype = formattype.upper()

        if formattype == 'JSON':
            json_encoded_tml = json.dumps([tml_obj])
        elif formattype == 'YAML':
            json_encoded_tml = json.dumps([tml_obj])
        # Assume it's just a Python object which will dump to JSON matching the TML format
        else:
            json_encoded_tml = json.dumps([tml_obj])
        import_policy = "ALL_OR_NONE"
        if validate_only is True:
            import_policy = 'VALIDATE_ONLY'
        tml_post_params = {"import_objects": json_encoded_tml,
                           "import_policy": import_policy,
                           "force_create": str(create_new_on_server).lower()}

        import_response = self.post_to_tml_endpoint(endpoint="metadata/tml/import", post_data=tml_post_params)
        return import_response.json()

    # Specific METADATA gets

    def get_pinboards(self):
        params = {'type': 'PINBOARD_ANSWER_BOOK'}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_questions(self):
        params = {'type': 'QUESTION_ANSWER_BOOK'}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    # Worksheets and Tables - how to distinguish
    def get_logical_tables(self):
        params = {'type': 'LOGICAL_TABLE'}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_worksheets(self):
        params = {'type': 'LOGICAL_TABLE', 'subtypes': 'WORKSHEET'}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_connections(self):
        params = {'type': 'DATA_SOURCE'}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    # Users

    def get_users(self):
        params = {'type': 'USER'}
        return self.get_from_endpoint("metadata/listobjectheaders", url_parameters=params)

    def get_groups(self):
        params = {'type': 'USER_GROUP'}
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
    def export_pinboard_pdf(self, id: str, visualization_ids):
        pass