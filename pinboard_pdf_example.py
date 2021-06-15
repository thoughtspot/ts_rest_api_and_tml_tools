import os
import requests.exceptions

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


pinboards = ts.get_pinboards()
first_pinboard_id = pinboards[4]["id"]
first_pinboard_name = pinboards[4]["name"]
print("First Pinboard Name: {}".format(first_pinboard_name))
print("First Pinboard ID: {}".format(first_pinboard_id))
try:
    pinboard_pdf = ts.export_pinboard_pdf(pinboard_id=first_pinboard_id, footer_text="Viz by the foot",
                                          cover_page=False, filter_page=False, landscape_or_portrait='PORTRAIT')
    new_file_name = "Test PDF.pdf"
    with open(new_file_name, 'bw') as fh:
        fh.write(pinboard_pdf)
except requests.exceptions.HTTPError as e:
    print(e)

ts.logout()
