import os
import requests.exceptions
import time
import datetime
from tsrest import TSRestV1

username = os.getenv('username')  # or type in yourself
password = os.getenv('password')  # or type in yourself
server = os.getenv('server')        # or type in yourself

ts: TSRestV1 = TSRestV1(server=server)
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

answers = ts.get_answers()
print(answers)
for a in answers:
    try:
        tml_string = ts.export_tml_string(a["id"], formattype='YAML')
    except Exception as e:
        print(e)
        continue
    with open("{}/answers/{}.tml".format(git_root_directory, a["id"]), 'w') as f:
        f.write(tml_string)


pinboards = ts.get_pinboards(sort='MODIFIED', sort_ascending=False)
current_time = datetime.datetime.now()
print(current_time.strftime("%Y-%m-%d %H:%M:%S"))

for pb in pinboards:
    epoch_time = int( pb['modified'] / 1000)
    modified_time = time.localtime(epoch_time)
    print(time.strftime("%Y-%m-%d %H:%M:%S", modified_time))
    print(epoch_time < time.time())
    try:
        tml_string = ts.export_tml_string(pb["id"], formattype='YAML')
    except Exception as e:
        print(e)
        continue
    with open("{}/pinboards/{}.tml".format(git_root_directory, pb["id"]), 'w') as f:
        f.write(tml_string)

print(pinboards)