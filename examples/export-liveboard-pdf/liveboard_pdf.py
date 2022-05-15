import os

import requests.exceptions

from thoughtspot import ThoughtSpot

username = os.getenv("username")  # or type in yourself
password = os.getenv("password")  # or type in yourself
server = os.getenv("server")  # or type in yourself

ts: ThoughtSpot = ThoughtSpot(server_url=server)
try:
    ts.login(username=username, password=password)
except requests.exceptions.HTTPError as e:
    print(e)
    print(e.response.content)


liveboards = ts.liveboard.list()
first_liveboard_id = liveboards[4]["id"]
first_liveboard_name = liveboards[4]["name"]
print("First Pinboard Name: {}".format(first_liveboard_name))
print("First Pinboard ID: {}".format(first_liveboard_id))
try:
    liveboard_pdf = ts.liveboard.pdf_export(
        liveboard_id=first_liveboard_id,
        footer_text="Viz by the foot",
        cover_page=False,
        filter_page=False,
        landscape_or_portrait="PORTRAIT",
    )
    new_file_name = "../Test PDF.pdf"
    with open(new_file_name, "bw") as fh:
        fh.write(liveboard_pdf)
except requests.exceptions.HTTPError as e:
    print(e)

ts.logout()
