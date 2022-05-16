"""
  This example shows how to localize worksheets and pinboards so you can create multiple versions.  For this scenarios
  the following must exist:
  * A data connection with data.  All worksheets will use the same, existing connection.
  * A worksheet and dependent content that has been "tagged" with localization tags.  This uses ${localize.token}
  * A file that maps the localized tokens to the strings to replace them with.  There will be a separate file for each
  * localization.
"""
import tempfile
import argparse
import shutil
import json
import os

import requests
import yaml
from deprecated.tml import *

from thoughtspot import ThoughtSpot

THOUGHTSPOT_GUID: str = "thoughtspot.guid"


#
# CLI
#


def get_args():
    """Returns the command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tsurl",
        type=str,
        required=True,
        help="full URL for the ThoughtSpot cluster.",
    )
    parser.add_argument(
        "--username",
        type=str,
        required=True,
        help="admin user that can access data.",
    )
    parser.add_argument("--password", type=str, required=True, help="admin password.")
    parser.add_argument(
        "--connection", type=str, required=True, help="unique ID (GUID) for the connection the worksheet uses."
    )
    parser.add_argument("--worksheet", type=str, required=True, help="unique ID (GUID) for the worksheet to localize.")
    parser.add_argument("--tokenfile", type=str, required=True, help="path to the file with the token replacements.")
    parser.add_argument(
        "--writeback",
        action="store_true",
        required=False,
        default=False,
        help="if true, write the resulting content back to ThoughtSpot as new content.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        required=False,
        choices=["validate", "create", "update"],
        default="validate",
        help="if writing back, specifies the if it's for validation, update, or create new.  " "Default is 'validate'",
    )
    parser.add_argument("--outfile", type=str, required=False, help="path to the file to write to.")
    parser.add_argument(
        "--include_dependencies",
        type=bool,
        default=False,
        required=False,
        help="if true will also localize all of the dependencies.",
    )

    cmdargs = parser.parse_args()

    if not valid_args(cmdargs):
        parser.print_help()
        exit(-1)

    return cmdargs


def valid_args(cmdargs) -> bool:
    """Does minimal validation on the arguments."""
    return cmdargs.tsurl and cmdargs.username and cmdargs.password and cmdargs.worksheet


#
# HELPER LOGIC
#


def get_worksheet(ts: ThoughtSpot, connection_guid: str, worksheet_guid: str) -> Worksheet:
    """
    :param ts: The connection to ThoughtSpot for API calls.
    :param connection_guid: GUID for the connection with the table to map to (not always the old connection)
    :param worksheet_guid: GUID for the worksheet that is being localized
    :return:  The worksheet object from ThoughtSpot.
    """

    # get the tables from the connection for mapping table names to FQNs (required)
    print(f"getting tables for connect {connection_guid}")
    destination_connection_existing_tables = ts.table.list_tables_for_connection(connection_guid=connection_guid)
    destination_connection_existing_tables_name_to_id_map = {}
    for t in destination_connection_existing_tables:
        destination_connection_existing_tables_name_to_id_map[t["name"]] = t["id"]
    print("Destination Connection - Existing Tables")
    print(destination_connection_existing_tables_name_to_id_map)

    # get the worksheet from the cluster (no dependencies yet)
    print(f"getting worksheet {worksheet_guid}")
    worksheet_tml = ts.tml.export_tml(guid=worksheet_guid)
    worksheet_tml = Worksheet(worksheet_tml)

    # clean up the TML
    worksheet_tml.remove_guid()  # always remove the old one since we are copying and not updating.
    worksheet_tml.remove_calendars()

    # Map table names to FQNs.
    worksheet_tml.remap_tables_to_new_fqn(destination_connection_existing_tables_name_to_id_map)

    return worksheet_tml


def replace_tokens(content_yaml: str, tokenfile: str) -> (str, str):
    """
    Returns the updated YAML with the tokens replace with values.
    :param content_yaml: The YAML for the content
    :param tokenfile: The path to the token file
    :return: The updated YAML and the GUID (or None).  The GUID is needed for updates.
    """

    # run through the config file and replace tokens.
    guid = None
    with open(tokenfile) as tkfile:
        for line in tkfile:
            line = line.strip()
            if line.startswith("#") or not "=" in line:
                continue
            else:
                (token, value) = map(lambda x: x.strip(), line.split("="))
                if token == THOUGHTSPOT_GUID:
                    guid = value
                content_yaml = re.sub(f"<%\s*{token}\s*%>", value, content_yaml)

    return content_yaml, guid


def write_yaml_file(outfile: str, content_yaml) -> None:
    """
    Writes the YAML to a file.
    :param outfile: The file path to write to.
    :param content_yaml:  The YAML to write to the file.
    """
    print(f"Writing TML to {outfile}")
    with open(outfile, "w") as of:
        of.writelines(content_yaml)


def write_yaml_to_thoughtspot(ts: ThoughtSpot, tokenfile: str, mode: str, content_yaml: str) -> None:

    if mode == "validate":
        validate_only = True
        create_new = False
    elif mode == "create":
        validate_only = False
        create_new = True
    else:  # update
        validate_only = False
        create_new = False

    print("Uploading TML to ThoughtSpot")
    response = ts.tml.upload_tml(
        yaml.load(content_yaml, Loader=yaml.Loader),
        create_new_on_server=create_new,
        validate_only=validate_only,
        formattype="YAML",
    )
    success = ts.tml.did_import_succeed(response)
    if success:
        print("\tsuccess")
    else:
        print(json.dumps(response, indent=4))

    try:
        add_guid_to_file(tokenfile, response["object"][0]["response"]["header"]["id_guid"])
    except IndexError as ie:
        print(f"Error adding GUID to file: {ie}")


def add_guid_to_file(tokenfile: str, guid: str) -> None:
    """
    Adds the GUID for the object to the token file for updates.
    :param tokenfile: The path to the token file.  The GUID will be appended.
    :param guid: The GUID for the object.
    :return: None
    """
    tmp, path = tempfile.mkstemp()

    with open(tokenfile, "r") as tkfile:
        try:
            added: bool = False
            for line in tkfile:
                if THOUGHTSPOT_GUID in line:
                    added = True
                    line = f"{THOUGHTSPOT_GUID}={guid}"
                os.write(tmp, bytearray(line, "UTF-8"))

            if not added:  # GUID wasn't there before, so add it now.
                os.write(tmp, bytearray(f"\n{THOUGHTSPOT_GUID}={guid}", "UTF-8"))

        except IOError as ioe:
            print(f"Error writing GUID: {ioe}")

    # clean up
    os.close(tmp)
    shutil.copy(path, tokenfile)
    os.remove(path)


#
#
#


def main_program(ts: ThoughtSpot, *, cmdargs: argparse.Namespace) -> None:
    """Gets a worksheet and related content (if including dependencies) and localizes."""

    # get the worksheet (and do needed cleanup
    worksheet_tml = get_worksheet(ts, cmdargs.connection, cmdargs.worksheet)

    # convert to text.
    worksheet_yaml = yaml.dump(worksheet_tml.tml)

    worksheet_yaml, worksheet_guid = replace_tokens(worksheet_yaml, cmdargs.tokenfile)

    # if this is an update, add the worksheet GUID
    mode = cmdargs.mode
    if mode == "update" and worksheet_guid:
        worksheet_yaml = f"guid: {worksheet_guid}\n{worksheet_yaml}"

    if cmdargs.outfile:
        write_yaml_file(cmdargs.outfile, worksheet_yaml)

    if cmdargs.writeback:
        write_yaml_to_thoughtspot(ts, cmdargs.tokenfile, mode, worksheet_yaml)

    if not (cmdargs.outfile or cmdargs.writeback):  # if no other activity, then just dump the results to stdout.
        print(worksheet_yaml)


if __name__ == "__main__":
    args = get_args()

    # Grab ThoughtSpot details from the environment, or type these in yourself.
    server = args.tsurl or os.getenv("TS_SERVER", "https://CHANGEME.thoughtspot.cloud/")
    username = args.username or os.getenv("TS_USERNAME", "CHANGE.ME")
    password = args.password or os.getenv("TS_PASSWORD", "CHANGE.ME")

    ts = ThoughtSpot(server_url=server)

    try:
        ts.login(username=username, password=password)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)
        return

    main_program(ts, cmdargs=args)
