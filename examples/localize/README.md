# Localize Content

This example allows you to localize content from a template.  There are two scenarios where this is useful.  The first is to localize names, descriptions, etc. to different languages.  The second is to easily provide different names, descriptions, etc. for different user groups.  

Currently, this script only supports a single worksheet at a time.  Updates are being made to support additional content types and content with dependencies.

## Approach

1. Create content that has names like `<% some.token %>`.  The tokens can be whatever, but the text must contain the brackets, percentages, and spaces.  
2. Create one or token mapping file.  This file will be of the format `some.token=Some Text`.  This file should have a line for each token to text value.  Lines starting with `#` will be ignored.
3. Run the script to localize the content.  The script can be run from any system with Python3 and access to the APIs.  The user must have access to all the content and the `manage data` privilege.

For example, a token file might look like:

~~~
worksheet.title=My Cool Worksheet
worksheet.description=This worksheet makes search easy.
~~~

Next, you would create a worksheet with tokens.  The title would be `<% worksheet.title %>` and the description would be `<% worksheet description %>`.

## Running the Script

Now that you have the worksheet and the token file, you can run the script.  The script will extract the TML for the content, update it based on the tokens and then validate, create new content, or update existing content based on the flags used.

~~~
usage: localize_content.py [-h] --tsurl TSURL --username USERNAME --password
                           PASSWORD --connection CONNECTION --worksheet
                           WORKSHEET --tokenfile TOKENFILE [--writeback]
                           [--mode {validate,create,update}]
                           [--outfile OUTFILE]
                           [--include_dependencies INCLUDE_DEPENDENCIES]

optional arguments:
  -h, --help            show this help message and exit
  --tsurl TSURL         full URL for the ThoughtSpot cluster.
  --username USERNAME   admin user that can access data.
  --password PASSWORD   admin password.
  --connection CONNECTION
                        unique ID (GUID) for the connection the worksheet
                        uses.
  --worksheet WORKSHEET
                        unique ID (GUID) for the worksheet to localize.
  --tokenfile TOKENFILE
                        path to the file with the token replacements.
  --writeback           if true, write the resulting content back to
                        ThoughtSpot as new content.
  --mode {validate,create,update}
                        if writing back, specifies the if it's for validation,
                        update, or create new. Default is 'validate'
  --outfile OUTFILE     path to the file to write to.
  --include_dependencies INCLUDE_DEPENDENCIES
                        if true will also localize all of the dependencies.
~~~

Author: [Bill Back](https://github.com/billdback-ts)