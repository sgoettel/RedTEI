# reddit-json2xml

Scripts to process Reddit data from compressed `.zst` files to TEI-XML.

## Overview

This project provides a pipeline, orchestrated by `run.py`, to transform Reddit comments into TEI-XML. The process includes extracting and filtering comments, grouping them into threads, and converting them into a TEI-valid XML format. The pipeline includes two processing modes, which allow either grouped or individual handling of comments.

## Usage

To run the main script, use:
```bash
python run.py path/to/subreddit.zst
# or to process each comment individually
python run.py --no-group path/to/subreddit.zst
```

The default mode groups all comments by thread (or "link") in a single JSON and XML file, while the `--no-group` flag saves each comment as a separate JSON and XML file.

### Supporting Scripts

-   [comment_tree.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/extractor/comment_tree.py): Extracts and organizes comments by thread.
-   [json2xml.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/extractor/json2xml.py): Converts JSON data into TEI-XML format.
-   [trim_username_comments.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/extractor/trim_username_comments.py): Filters and prepares comments by removing certain elements 
-   [validate.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/extractor/validate.py): Validates the XML output against a TEI schema.

For more details on how the filtering proccess etc. works see the [Wiki](https://git.zdl.org/koerber/reddit-json2xml/wiki).

## Testing

Run tests with ``pytest``.

For [coverage](https://coverage.readthedocs.io/en/7.4.4/) analysis (currently 79%) use:

```bash
coverage run -m pytest
coverage report -m --include="extractor/*"
```

## Examples

In the [examples/demo](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples) directory, you’ll find sample JSON files in two folders: `grouped` and `ungrouped`. To see the conversion process, run:

```bash
python extractor/json2xml.py
```

The JSON samples will be processed and converted into XML files in their respective folders (`grouped` or `ungrouped`).


## Installation

To set up the environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```
