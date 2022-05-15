import os

import requests.exceptions

from thoughtspot import MetadataNames, ThoughtSpot


def main_program(ts: ThoughtSpot) -> None:
    """
    Run the main program logic.
    """
    # Example of deleting a Liveboard with a known GUID
    lb_guid = ""
    # metadata/delete requires the object_type and a List of GUIDs to delete
    ts.tsrest.metadata_delete(object_type=MetadataNames.LIVEBOARD, guids=[lb_guid])

    # You can chain this with the metadata/list calls to remove a whole set of items
    lbs_with_a_tag = ts.tsrest.metadata_list(object_type=MetadataNames.LIVEBOARD, tagname=["Old Stuff"])
    guids_to_delete = []
    for lb in lbs_with_a_tag:
        guids_to_delete.append(lb["id"])

    ts.tsrest.metadata_delete(object_type=MetadataNames.LIVEBOARD, guids=guids_to_delete)

    # Alternatively, removing all sharing and switching ownership to a "dead content account" with
    # ts.tsrest.user_transfer_ownership() is a safer move before deleting any content


if __name__ == "__main__":
    # Grab ThoughtSpot details from the environment, or type these in yourself.
    server = os.getenv("TS_SERVER", "https://CHANGEME.thoughtspot.cloud/")
    username = os.getenv("TS_USERNAME", "CHANGE.ME")
    password = os.getenv("TS_PASSWORD", "CHANGE.ME")

    ts = ThoughtSpot(server_url=server)

    try:
        ts.login(username=username, password=password)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.content)
        return

    main_program(ts)
