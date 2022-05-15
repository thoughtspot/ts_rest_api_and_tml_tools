# ThoughtSpot REST API Examples

`ts_rest_api_and_tml_tools` is a thin functional wrapper around the V1 REST API. Included in this repository is the pip installable wrapper, as well as example recipes for many common workflows using the API or interacting with TML and your __ThoughtSpot__ platform.

__All code and examples are intended only as a starting point! Nothing is production-ready out of the box.__ They are intended to help give you an understanding of API capabilities and what a code-supported workflow might look like.


## Installing & Getting Started

If you'd like to run the examples directly, you must install the wrapper client. This requires at least __`python` version 3.6.8__.

```shell
$ python -m venv .ts-venv
$ source .ts-venv/bin/activate  # or windows:    .ts-venv/Scripts/activate 
(.ts-venv) $ pip install https://github.com/thoughtspot/archive/ts_rest_api_and_tml_tools.zip
```


### A note about Compatibility

`ts_rest_api_and_tml_tools` is developed and tested __only against the `tspublic/v1` endpoints__ which are generally available on __ThoughtSpot Cloud__ or [begin appearing in __ThoughtSpot__ 7.1.1 and later][ts-docs-v1-changelog].

*The V1 REST API is not versioned, so if you run on __ThoughtSpot__ Software please check your documentation for available endpoints.*

After you've installed the wrapper, you may check your deployment branch and current version by running the below command.

```shell
(.ts-venv) $ ts-examples info
```

To view the full list of V1 endpoints included, please view the separate repository at [`thoughtspot_rest_api_v1`][ts-rest-v1-repo].


## Using the Examples

Each example in the [`/examples` directory][here-examples] is self-contained under it's own sub-directory, along with a `README` to explain its utility. In order to run it, you may copy the sub-directory contents to your own local machine and execute it like any other python file.

All examples are written in Python. We have chosen python due to its readability, but you may write against the __ThoughtSpot__ APIs in any language that supports HTTP session management.

For a library built on top of the API that handles support for older Software versions, has built-out utilities, and a full CLI, please see [__CS Tools__ documentation][cs-tools-docs] or star us on [GitHub][cs-tools-gh].


## V2 REST API

The V2 REST API is [currently in __Public Preview__][ts-docs-v2-intro]. The framework is built upon the existing core API functionality and resource representation model, and offers several new features and enhancements.

 - Enhanced usability and developer experience
 - Language-specific SDK and client libraries
 - Token-based authentication and authorization
 - Consistent request and response workflow
 - Simplified resource collections and endpoint categories

If you are an existing user with a valid __ThoughtSpot Everywhere__ Edition license, you can contact __ThoughtSpot Support__ to enable the REST API Playground and SDK feature on your cluster.


## Want to Contribute an Example?

Contributions to our examples are encouraged and very welcome! ❤️

To get started, follow the steps below..

 1. Clone this repo `git clone https://github.com/thoughtspot/ts_rest_api_and_tml_tools` and `cd` into the directory
 2. Setup a virtual environment `python -m venv .ts-dev-venv` and activate it
 3. Install the wrapper `(.ts-dev-venv) $ pip install .[dev]`
 4. Branch from `master`, write some code, commit early and often!
 5. Before submitting a PR, run `(.ts-dev-venv) $ ts-examples prep --help`

 Please submit only a single example at a time. If you would like to contribute multiple examples, please open an additional PR for each example.


[here-examples]: ./examples
[ts-rest-v1-repo]: https://github.com/thoughtspot/thoughtspot_rest_api_v1_python
[ts-docs-v1-changelog]: https://developers.thoughtspot.com/docs/?pageid=rest-v1-changelog
[ts-docs-v2-intro]: https://developers.thoughtspot.com/docs/?pageid=rest-api-v2 
[cs-tools-docs]: https://thoughtspot.github.io/cs_tools/
[cs-tools-gh]: https://github.com/thoughtspot/cs_tools