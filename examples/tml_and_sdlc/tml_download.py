import os
import requests.exceptions
import time
import datetime
from thoughtspot import ThoughtSpot, MetadataNames

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)

# Without filtering at the API level for what is recently modified, we'll simply sort the first responses
# then only look at what has changed since the last time

# This is the root directory, and then we have sub-directories for Pinboards, Answers, etc.
# for organizational purposes
git_root_directory = os.getenv('git_directory')  # or type in yourself


# This will overwrite existing files downloaded before, which is intentional to
def download_objects_to_directory(root_directory, directory_name, object_type,
                                  object_guid_list=None, category_filter=None):
    # Mapping of the metadata object types to the directory to save them to
    object_type_directory_map = {
        MetadataNames.LIVEBOARD: 'liveboard',
        MetadataNames.ANSWER: 'answer',
        MetadataNames.TABLE: 'table',
        MetadataNames.WORKSHEEET: 'worksheet'
    }

    objs = ts.tsrest.metadata_listobjectheaders(object_type=object_type, sort='MODIFIED', sort_ascending=False,
                                                category=category_filter, fetchids=object_guid_list)
    # Export one object at a time as YAML, for ease of parsing and saving
    # The REST APIs do allow requesting more than one TML object at a time, but you would need to separate
    # them out in the response and parse the GUIDs from there
    for obj in objs:
        guid = obj['id']
        try:
            tml_string = ts.tml.export_tml_string(guid=guid, formattype='YAML')
        except Exception as e:
            print(e)
            continue
        # Naming pattern is {Git root}/{object_type}/{GUID}.{object_type}.tml
        with open("{}/{}/{}.{}.tml".format(root_directory, directory_name, guid,
                                           object_type_directory_map[object_type]), 'w') as f:
            f.write(tml_string)


# filtering based on time
#pinboards = ts.pinboard.list(sort='MODIFIED', sort_ascending=False)
#current_time = datetime.datetime.now()
#print(current_time.strftime("%Y-%m-%d %H:%M:%S"))

#for pb in pinboards:
#    epoch_time = int(pb['modified'] / 1000)
#    modified_time = time.localtime(epoch_time)
#    print(time.strftime("%Y-%m-%d %H:%M:%S", modified_time))
#    print(epoch_time < time.time())
#    try:
#        tml_string = ts.tml.export_tml_string(pb["id"], formattype='YAML')
#    except Exception as e:
#        print(e)
#        continue
#    with open("{}/pinboards/{}.tml".format(git_root_directory, pb["id"]), 'w') as f:
#        f.write(tml_string)

#print(pinboards)