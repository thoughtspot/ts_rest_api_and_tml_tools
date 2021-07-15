"""
  This example shows how to localize worksheets and pinboards so you can create multiple versions.  For this scenarios
  the following must exist:
  * A data connection with data.  All worksheets will use the same, existing connection.
  * A worksheet and dependent content that has been "tagged" with localization tags.  This uses ${localize.token}
  * A file that maps the localized tokens to the strings to replace them with.  There will be a separate file for each
  * localization.
"""
import argparse
import re
import requests

from thoughtspot import ThoughtSpot
from tml import *


def get_args():
    """Returns the command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument("--tsurl", type=str, required=True,
                        help="Full URL for the ThoughtSpot cluster.")
    parser.add_argument("--username", type=str, required=True,
                        help="Admin user that can access data.")
    parser.add_argument("--password", type=str, required=True,
                        help="Admin password.")
    parser.add_argument("--worksheet", type=str, required=True,
                        help="GUID for the worksheet to localize.")
    parser.add_argument("--tokenfile", type=argparse.FileType('r'), required=True,
                        help="Path to the file with the token replacements.")
    parser.add_argument("--writeback", type=bool, required=False,
                        help="If true, write the resulting content back to ThoughtSpot.")
    parser.add_argument("--outfile", type=str, required=False,
                        help="Path to the file to write to.")
    parser.add_argument("--include_dependencies", type=bool, default=False, required=False,
                        help="If true will also localize all of the dependencies.")

    args = parser.parse_args()

    if not valid_args(args):
        parser.print_help()
        exit(-1)

    return args


def valid_args(args):
    """Does minimal validation on the arguments."""
    return args.tsurl and args.username and args.password and args.worksheet


def localize_content(args):
    """Gets a worksheet and related content (if including dependencies) and localizes."""

    # Create the TS interface
    ts: ThoughtSpot = ThoughtSpot(server_url=args.tsurl)
    try:
        ts.login(username=args.username, password=args.password)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)

    # get the worksheet from the cluster (no dependencies yet)
    print(f"getting worksheet {args.worksheet}")
    tml = ts.tml.export_tml_string(guid=args.worksheet, formattype="YAML")

    # run through the config file and replace.
    for line in args.tokenfile:
        (token, value) = map(lambda x: x.strip(), line.split('='))
        tml = re.sub(f"<%\s*{token}\s*%>", value, tml)

    # write to output file.
    if args.outfile:
        print(f"Writing TML to {args.outfile}")
        with open(args.outfile, "w") as outfile:
            outfile.writelines(tml)

    if not (args.outfile or args.writeback):  #  if no other activity, then just dump the results to stdout.
        print(tml)


if __name__ == "__main__":
    args = get_args()
    localize_content(args)

