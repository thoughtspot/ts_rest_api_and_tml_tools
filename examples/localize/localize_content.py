"""
  This example shows how to localize worksheets and pinboards so you can create multiple versions.  For this scenarios
  the following must exist:
  * A data connection with data.  All worksheets will use the same, existing connection.
  * A worksheet and dependent content that has been "tagged" with localization tags.  This uses ${localize.token}
  * A file that maps the localized tokens to the strings to replace them with.  There will be a separate file for each
  * localization.
"""
import argparse
import json
import re
import requests
import yaml

from thoughtspot import ThoughtSpot
from tml import *


def get_args():
    """Returns the command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument("--tsurl", type=str, required=True,
                        help="full URL for the ThoughtSpot cluster.")
    parser.add_argument("--username", type=str, required=True,
                        help="admin user that can access data.")
    parser.add_argument("--password", type=str, required=True,
                        help="admin password.")
    parser.add_argument("--connection", type=str, required=True,
                        help="unique ID (GUID) for the connection the worksheet uses.")
    parser.add_argument("--worksheet", type=str, required=True,
                        help="unique ID (GUID) for the worksheet to localize.")
    parser.add_argument("--tokenfile", type=argparse.FileType('r'), required=True,
                        help="path to the file with the token replacements.")
    parser.add_argument("--writeback", action="store_true", required=False, default=False,
                        help="if true, write the resulting content back to ThoughtSpot as new content.")
    parser.add_argument("--outfile", type=str, required=False,
                        help="path to the file to write to.")
    parser.add_argument("--validate", action="store_true", default=False,
                        help="if set, will only validate the TML and not save it.")
    parser.add_argument("--include_dependencies", type=bool, default=False, required=False,
                        help="if true will also localize all of the dependencies.")

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

    # get the tables from the connection for mapping table names to FQNs (required)
    print(f"getting tables for connect {args.connection}")
    destination_connection_existing_tables = ts.table.list_tables_for_connection(connection_guid=args.connection)
    destination_connection_existing_tables_name_to_id_map = {}
    for t in destination_connection_existing_tables:
        destination_connection_existing_tables_name_to_id_map[t['name']] = t['id']
    print("Destination Connection - Existing Tables")
    print(destination_connection_existing_tables_name_to_id_map)

    # get the worksheet from the cluster (no dependencies yet)
    print(f"getting worksheet {args.worksheet}")
    worksheet_tml = ts.tml.export_tml(guid=args.worksheet)
    worksheet_tml = Worksheet(worksheet_tml)
    worksheet_tml.remove_guid()
    worksheet_tml.remove_calendars()
    print(worksheet_tml)
    worksheet_tml.remap_tables_to_new_fqn(destination_connection_existing_tables_name_to_id_map)

    # convert to text.
    worksheet_yaml = yaml.dump(worksheet_tml.tml)

    # run through the config file and replace.
    for line in args.tokenfile:
        (token, value) = map(lambda x: x.strip(), line.split('='))
        worksheet_yaml = re.sub(f"<%\s*{token}\s*%>", value, worksheet_yaml)

    # write to output file.
    if args.outfile:
        print(f"Writing TML to {args.outfile}")
        with open(args.outfile, "w") as outfile:
            outfile.writelines(worksheet_yaml)

    if args.writeback:
        print("Uploading TML to ThoughtSpot")
        response = ts.tml.upload_tml(yaml.load(worksheet_yaml), create_new_on_server=True, validate_only=args.validate, formattype="YAML")
        success = ts.tml.did_import_succeed(response)
        if success:
            print("\tsuccessfully uploaded")
        else:
            print(json.dumps(response, indent=4))

    if not (args.outfile or args.writeback):  # if no other activity, then just dump the results to stdout.
        print(worksheet_yaml)


if __name__ == "__main__":
    args = get_args()
    localize_content(args)

