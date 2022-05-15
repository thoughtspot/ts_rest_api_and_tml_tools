import sys
import os

import oyaml as yaml

# import argparse

# from tml import *

# Command line script to parse local directory with TML files and display back useful information
# Necessary when storing TML just with GUID for filename in a SDLC process

# Look for a directory or filename as 1st argument, otherwise use local working directory
if len(sys.argv) == 1:
    directory = os.getcwd()
else:
    directory = sys.argv[1]
    # Correct for additional slash at the end
    if directory[-1] == "/":
        directory = directory[0:-1]


def parse_tml_file(filename, directory=None):
    if filename.find(".tml") != -1:
        if directory is None:
            fh = open(filename, "r")
        else:
            fh = open(directory + "/" + filename, "r")
        # print('Opened {}'.format(filename))
        yaml_tml = fh.read()
        fh.close()
        # Using pyyaml here
        tml_dict = yaml.load(yaml_tml, Loader=yaml.Loader)
        content_type = None
        for key in tml_dict:
            if key in ["guid", "id"]:
                continue
            else:
                content_type = key
        # Generic TML object can get guid and name
        guid = tml_dict["guid"]
        content_name = None
        if "name" in tml_dict[content_type]:
            content_name = tml_dict[content_type]["name"]
        # tml_obj = TML(tml_dict)
        print("{}|{}|{}".format(filename, content_name, guid))


# parse single file
if directory.find(".tml") != -1:
    parse_tml_file(filename=directory)
else:
    dir_list = os.listdir(directory)
    for filename in dir_list:
        parse_tml_file(filename=filename, directory=directory)
