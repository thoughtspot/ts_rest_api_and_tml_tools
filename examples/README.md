# Examples Repository

The example scripts within this directory show practical use cases of the various aspects of the library.

__All code and examples are intended only as a starting point! Nothing is production-ready out of the box.__ They are intended to help give you an understanding of API capabilities and what a code-supported workflow might look like.

---

 - [REST API Workflow](./rest-api-workflow/README.md): *Basic example showing many ways to use the REST API library. Start here to learn the syntax and capabilities*
 - [Liveboard PDF Export](./export-liveboard-pdf/README.md): *Simple example of programmatically exporting a PDF of a Liveboard*
 - [Auditing](./audit-objects/README.md): *Set of examples using the TS Cloud REST APIs to retrieve sharing permissions on various objects.*
 - [Deletion](./delete-object/README.md): *lorem ipsum*
 - [Dependencies](./dependencies/README.md): *lorem ipsum*
 - [Tagging](./tag-objects/README.md): *lorem ipsum*
 - [Import Tables](./import-tables/README.md): *Advanced script to bring in all tables from a given schema, rather than having to select them all via the UI.*
 - [Localization](./localize/README.md): *Use token manipulation to customize TML files, producing versions in new languages from a single template*
 - [SDLC Workflow](./tml_and_sdlc/README.md): *Manipulate TML files and incorporate them into SDLC tools such as git*

---

## How do I use the examples?

If you'd like to run the examples directly, you must first [install the wrapper client][here-install].

Copy the contents of any example script into your own `.py` file.

To configure the script, you can either set three environment variables or skip to the bottom of any of the example scripts and modify the following lines.

```python

if __name__ == "__main__":
    # Grab ThoughtSpot details from the environment, or type these in yourself.
    server = os.getenv("TS_SERVER", "https://CHANGEME.thoughtspot.cloud/")
    username = os.getenv("TS_USERNAME", "CHANGE.ME")
    password = os.getenv("TS_PASSWORD", "CHANGE.ME")

```

Once you have entered your configuration details, run the script directly from `python`.

```shell
(.ts-venv) $ python /some/path/to/audit_object_access.py
```

### Environment Variables

`TS_SERVER` - this is the web URL of your __ThoughtSpot__ platform. If you are running the scripts against your __ThoughtSpot Cloud__ cluster, only replace the `CHANGEME` subdomain. If you are using __ThoughtSpot Software__, you can replace the whole line `https://CHANGEME.thoughtspot.cloud/`.

`TS_USERNAME` - this is the `username` of a local account, which you can create using the Admin panel of your __ThoughtSpot__ cluster. The scripts ran will assume the security context which you assign to this user. If this user has Administrator privileges, so will that script.

`TS_PASSWORD` - this is the password of the user defined in `TS_USERNAME`.


[here-install]: ../README.md#
