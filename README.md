# RedTEI

This project provides a pipeline, orchestrated by `run.py`, to transform Reddit comments sourced from the Pushshift archive into TEI-XML format.

**We welcome any form of contribution!  Suggestions for improvement, bug reports, code contributions - every contribution is welcome and helps to further develop the project.**

## Installation

To set up the environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

## Usage

To run the main script, use:
```bash
python run.py path/to/subreddit.zst
# or to process (and save) each comment individually
python run.py --no-group path/to/subreddit.zst
```

The default mode groups all comments by thread (or "link") in a single JSON and XML file, while the `--no-group` flag saves each comment as a separate JSON and XML file.

## Examples

In the [examples/demo](https://github.com/sgoettel/RedTEI/tree/master/examples/demo) directory, you’ll find sample JSON files in two folders: `grouped` and `ungrouped`. To see the conversion process, run:

```bash
python -m extractor.json2xml
```

The JSON samples will be processed and converted into XML files in their respective folders (`grouped` or `ungrouped`).

### Supporting Scripts

-   [trim_username_comments.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/trim_username_comments.py): Filters and prepares comments by removing certain elements (deleted content, quotes, "remindme" bots, URLs).
-   [comment_tree.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/comment_tree.py): Extracts and organizes comments by thread from the filtered `.zst` file.
-   [comment_processing.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/comment_processing.py): Handles processing of individual comments (`--no-group` mode) and full threads.
-   [json2xml.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/json2xml.py): Converts JSON data into TEI-XML format.
-   [validate.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/validate.py): Validates the XML output against a TEI schema.
-   [utils.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/utils.py): Provides utility functions for file management, batch processing and data validation.

For more details on how the filtering proccess etc. works see the [Wiki](https://git.zdl.org/koerber/reddit-json2xml/wiki).

## Testing

Run tests with ``pytest``.

For [coverage](https://coverage.readthedocs.io/en/7.4.4/) analysis (currently 80%) use:

```bash
coverage run -m pytest
coverage report -m --include="extractor/*"
```



---

# Table of Contents
- [About the Project](#about-the-project)
- [Datasets](#datasets)
- [Data Structure](#data-structure)
  - [Explanation of Key JSON Keys](#explanation-of-key-json-keys)
- [Processing](#processing)
  - [Processing Overview](#processing-overview)
  - [1. Filtering JSON Objects](#1-filtering-json-objects)
  - [2. Extraction to JSON Files](#2-extraction-to-json-files)
  - [3. Conversion to XML](#3-conversion-to-xml)
- [Usage / Application](#usage--application)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Execution](#execution)
  - [Output Directory Structure](#output-directory-structure)


## About the Project

This project provides a pipeline, orchestrated by `run.py`, to transform Reddit comments sourced from the Pushshift archive into TEI-XML format. By using this pipeline, we created the [*Reddit-d* corpus](https://www.dwds.de/d/korpora/reddit) for the *Digital Dictionary of the German Language* ([DWDS](https://www.dwds.de/)). This corpus is based on data from the top 40 German-speaking subreddits available in the Pushshift archive (dumps up to 2023-12-31 are available on [academictorrent](https://academictorrents.com/details/56aa49f9653ba545f48df2e33679f014d2829c10), data up to the end of 2024 is also available).

The primary purpose of this pipeline is to facilitate the creation of corpora from Reddit data. The pipeline contains several key processing steps, including extracting and filtering comments, with an option to group them into threads, before final conversion into a TEI-valid XML format.



## Data Structure

The Pushshift archives in zst format contain NDJSON files, which represent a sequence of JSON objects. Each JSON object represents a single Reddit comment.

### JSON Keys

*   **author**: Username of the author.
*   **author_fullname**: Unique ID of the author.
*   **body**: The actual content of the comment.
*   **created_utc**: Time of creation of the comment in UTC, specified as a Unix timestamp (seconds since January 1, 1970, 00:00:00 UTC).
*   **id**: Unique ID of the comment.
*   **link_id**: ID of the parent main post (thread) to which the comment belongs. *Used to group all comments of a thread.*
*   **parent_id**: ID of the direct ancestor (parent) of the comment. Starts with `t1_` if the comment is a reply to another comment; starts with `t3_` if it is a reply to the main post (thread).
*   **permalink**: Permanent link (URL) to the comment on Reddit. *Allows direct access to the comment in the Reddit context.*
*   **retrieved_on / retrieved_utc**: Time of retrieval and archiving of the comment from Reddit, specified as a Unix timestamp. *Serves to document the time of data collection.*
*   **score**: Net score of the comment (number of upvotes minus downvotes).
*   **subreddit**: Name of the subreddit in which the comment was written (e.g., `r/de`).
*   **subreddit_id**: Unique ID of the subreddit.


## Processing

There are two main processing modes:

- **Grouped Mode (default):** This mode is the default setting. Comments are grouped by Reddit threads. All comments of a thread are stored together in a single XML file.
- **No-Group Mode (`--no-group`):** When this mode is activated, each comment is processed individually. Each comment is stored in a separate XML file, without grouping by threads.

The processing is divided into the following steps:

1.  Filtering JSON objects
2.  Extraction to JSON files
3.  Conversion to XML files


### 1. Filtering JSON Objects

**Script:** `trim_username_comments.py`

This script filters and modifies JSON objects directly in the `.zst` archives before they are further processed. JSON objects are excluded from further processing under the following conditions:

*   The value of the `"body"` key is `"[removed]"`, `"[deleted]"`, or `"[removed by reddit]"`.
*   The value of the `"author"` key corresponds to a bot name listed in the `src/config/botlist.txt` file.
*   The comment text is a request to the RemindMeBot (e.g., `!RemindMe 2 days`).
*   The comment consists only of a plaintext URL or, after removing all URLs, contains only `[URL]` placeholders (possibly followed by punctuation marks, spaces, or newlines, e.g., `[URL]!!!`).

In addition, the following modifications are made to the comment text (`"body"`):

*   **Remove quotes:** Removes quotations from comments.
*   **Remove URLs:**
    *   Plaintext URLs are replaced with `[URL]` (e.g., `http://example.com` → `[URL]`).
    *   Markdown URLs are removed, keeping the link text unless the text itself is also a URL (e.g., `[Example](https://example.com)` → `Example`; `[http://example.com](http://example.com)` → `[URL]`).
*   **Remove inline formatting:**
    *   **Bold:** Double asterisks `**` are removed, the text remains (e.g., `**Text**` → `Text`).
    *   *Italic:* Single asterisks `*` are removed, the text remains (e.g., `*Text*` → `Text`).
    *   ~~Strikethrough~~: Tildes `~~` and the strikethrough text are removed (e.g., `~~Text~~` → *(empty)*).
*   **Remove Zero-Width Spaces:** All Zero-Width Spaces (`\u200B`, `​`, `&#x200B;`) are removed.
*   **Reduce Multiple Newlines:** Consecutive newlines are reduced to a single newline.
*   **Discard Empty Comments:** Comments that are empty or consist only of whitespace after all modifications are not processed further.

All filtering and modifications (except inline formatting) are documented in a log file `filtered_log_{input_filename}.txt`. Since a comment can meet multiple filter criteria (e.g., contain a quote and a URL), a comment may appear multiple times in the log file if multiple filter actions were applied.


### 2. Extraction to JSON Files

**Scripts:** `comment_tree.py` & `comment_processing.py`

These scripts extract comments from filtered `.zst` files and store them in JSON format. The type of storage varies depending on the selected processing mode:

**Grouped Mode (default):**

*   Comments are grouped into threads based on the `link_id`.
*   All comments of a thread are stored in a single JSON file as a list of JSON objects.
*   Filename: `{link_id}_flat.json` (e.g., `10ax890_flat.json`).
*   The original tree structure of comments within the thread is **not** preserved; the comments are stored as a flat list.

**No-Group Mode (`--no-group`):**

*   Each comment is processed individually and stored in a separate JSON file.
*   Each JSON file contains a single JSON object (the comment).
*   Filename: `{link_id}_{comment_id}.json` (e.g., `10wugax_jepcf1r.json`).


### 3. Conversion to XML

**Script:** `json2xml.py`

This script converts the JSON files into TEI-XML format. The XML structure depends on the processing mode:

**Grouped Mode (default):**

*   Creates one XML file per thread.
*   **TEI Header:** Contains metadata about the thread (title, subreddit, date of last comment, thread URL), extracted from the first comment in the JSON file.
*   **XML Body:**
    *   Comments are grouped in a `<list>` element within a `<div type="comments">`.
    *   Each comment is represented as an `<item>` element within the `<list>`.
    *   `<item>` elements contain:
        *   Comment text
        *   `<date>` (creation date)
        *   `<name>` (author)
        *   `source` attribute (comment URL)
        *   Line breaks in the comment text are encoded as `<lb/>`.

**No-Group Mode (`--no-group`):**

*   Creates one XML file per comment.
*   **TEI Header:** Contains more detailed metadata about the comment and thread (title of the thread, subreddit, date of the comment, thread and comment URLs).
*   **XML Body:**
    *   Each comment is placed as a single `<p>` element directly in the `<body>`.
    *   The `<p>` element contains the comment text. No `<item>`, `<list>`, `<date>`, or `<name>` elements in the comment body.
    *   Line breaks in the comment text are encoded as `<lb/>`.

The script `validate.py` is used to check the validity of the XML files.


### Installation

To set up the environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Usage

To run the main script, use:
```bash
python run.py path/to/subreddit.zst
# or to process (and save) each comment individually
python run.py --no-group path/to/subreddit.zst
```

The default mode groups all comments by thread (or "link") in a single JSON and XML file, while the `--no-group` flag saves each comment as a separate JSON and XML file.

### Examples

In the [examples/demo](https://github.com/sgoettel/RedTEI/tree/master/examples/demo) directory, you’ll find sample JSON files in two folders: `grouped` and `ungrouped`. To see the conversion process, run:

```bash
python -m extractor.json2xml
```

The JSON samples will be processed and converted into XML files in their respective folders (`grouped` or `ungrouped`).

### Testing

Run tests with ``pytest``.

For [coverage](https://coverage.readthedocs.io/en/7.4.4/) analysis (currently 80%) use:

```bash
coverage run -m pytest
coverage report -m --include="extractor/*"
```

### Output Directory Structure

After successful execution of the pipeline, the generated JSON and XML files are stored in the following directory structure:

```
subreddits/
└── <subreddit>_<mode>/
    ├── <subreddit>_json_<mode>/
    │   ├── 00001/
    │   │   ├── ...JSON files...
    │   ├── 00002/
    │   │   ├── ...JSON files...
    │   └── ...
    └── <subreddit>_xml_<mode>/
        ├── 00001/
        │   ├── ...XML files...
        ├── 00002/
        │   ├── ...XML files...
        └── ...
```

The JSON and XML files are stored in numbered subdirectories within the respective `_json_...` and `_xml_...` directories.
# RedTEI

This project provides a pipeline, orchestrated by `run.py`, to transform Reddit comments sourced from the Pushshift archive into TEI-XML format.

**We welcome any form of contribution!  Suggestions for improvement, bug reports, code contributions - every contribution is welcome and helps to further develop the project.**

## Installation

To set up the environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

## Usage

To run the main script, use:
```bash
python run.py path/to/subreddit.zst
# or to process (and save) each comment individually
python run.py --no-group path/to/subreddit.zst
```

The default mode groups all comments by thread (or "link") in a single JSON and XML file, while the `--no-group` flag saves each comment as a separate JSON and XML file.

## Examples

In the [examples/demo](https://github.com/sgoettel/RedTEI/tree/master/examples/demo) directory, you’ll find sample JSON files in two folders: `grouped` and `ungrouped`. To see the conversion process, run:

```bash
python -m extractor.json2xml
```

The JSON samples will be processed and converted into XML files in their respective folders (`grouped` or `ungrouped`).

### Supporting Scripts

-   [trim_username_comments.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/trim_username_comments.py): Filters and prepares comments by removing certain elements (deleted content, quotes, "remindme" bots, URLs).
-   [comment_tree.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/comment_tree.py): Extracts and organizes comments by thread from the filtered `.zst` file.
-   [comment_processing.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/comment_processing.py): Handles processing of individual comments (`--no-group` mode) and full threads.
-   [json2xml.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/json2xml.py): Converts JSON data into TEI-XML format.
-   [validate.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/validate.py): Validates the XML output against a TEI schema.
-   [utils.py](https://github.com/sgoettel/RedTEI/blob/master/extractor/utils.py): Provides utility functions for file management, batch processing and data validation.

For more details on how the filtering proccess etc. works see the [Wiki](https://git.zdl.org/koerber/reddit-json2xml/wiki).

## Testing

Run tests with ``pytest``.

For [coverage](https://coverage.readthedocs.io/en/7.4.4/) analysis (currently 80%) use:

```bash
coverage run -m pytest
coverage report -m --include="extractor/*"
```

---

# Table of Contents
- [About the Project](#about-the-project)
- [Data Structure](#data-structure)
  - [JSON Keys](#json-keys)
- [Processing](#processing)
  - [Processing Overview](#processing-overview)
  - [1. Filtering JSON Objects](#1-filtering-json-objects)
  - [2. Extraction to JSON Files](#2-extraction-to-json-files)
  - [3. Conversion to XML](#3-conversion-to-xml)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Testing](#testing)
- [Output Directory Structure](#output-directory-structure)


## About the Project

This project provides a pipeline, orchestrated by `run.py`, to transform Reddit comments sourced from the Pushshift archive into TEI-XML format.  By using this pipeline, we created the [*Reddit-d* corpus](https://www.dwds.de/d/korpora/reddit) for the *Digital Dictionary of the German Language* ([DWDS](https://www.dwds.de/)).  This corpus is based on data from the top 40 German-speaking subreddits available in the Pushshift archive (dumps up to 2023-12-31 are available on [academictorrent](https://academictorrents.com/details/56aa49f9653ba545f48df2e33679f014d2829c10), data up to the end of 2024 is also available).

The primary purpose of this pipeline is to facilitate the creation of corpora from Reddit data. The pipeline contains several key processing steps, including extracting and filtering comments, with an option to group them into threads, before final conversion into a TEI-valid XML format.



## Data Structure

The Pushshift archives in zst format contain NDJSON files, which represent a sequence of JSON objects. Each JSON object represents a single Reddit comment.

### JSON Keys

*   **author**: Username of the author.
*   **author_fullname**: Unique ID of the author.
*   **body**: The actual content of the comment.
*   **created_utc**: Time of creation of the comment in UTC, specified as a Unix timestamp (seconds since January 1, 1970, 00:00:00 UTC).
*   **id**: Unique ID of the comment.
*   **link_id**: ID of the parent main post (thread) to which the comment belongs. *Used to group all comments of a thread.*
*   **parent_id**: ID of the direct ancestor (parent) of the comment. Starts with `t1_` if the comment is a reply to another comment; starts with `t3_` if it is a reply to the main post (thread).
*   **permalink**: Permanent link (URL) to the comment on Reddit. *Allows direct access to the comment in the Reddit context.*
*   **retrieved_on / retrieved_utc**: Time of retrieval and archiving of the comment from Reddit, specified as a Unix timestamp. *Serves to document the time of data collection.*
*   **score**: Net score of the comment (number of upvotes minus downvotes).
*   **subreddit**: Name of the subreddit in which the comment was written (e.g., `r/de`).
*   **subreddit_id**: Unique ID of the subreddit.


## Processing

There are two main processing modes:

- **Grouped Mode (default):** This mode is the default setting. Comments are grouped by Reddit threads. All comments of a thread are stored together in a single XML file.
- **No-Group Mode (`--no-group`):** When this mode is activated, each comment is processed individually. Each comment is stored in a separate XML file, without grouping by threads.

The processing is divided into the following steps:

1.  Filtering JSON objects
2.  Extraction to JSON files
3.  Conversion to XML files


### 1. Filtering JSON Objects

**Script:** `trim_username_comments.py`

This script filters and modifies JSON objects directly in the `.zst` archives before they are further processed. JSON objects are excluded from further processing under the following conditions:

*   The value of the `"body"` key is `"[removed]"`, `"[deleted]"`, or `"[removed by reddit]"`.
*   The value of the `"author"` key corresponds to a bot name listed in the `src/config/botlist.txt` file.
*   The comment text is a request to the RemindMeBot (e.g., `!RemindMe 2 days`).
*   The comment consists only of a plaintext URL or, after removing all URLs, contains only `[URL]` placeholders (possibly followed by punctuation marks, spaces, or newlines, e.g., `[URL]!!!`).

In addition, the following modifications are made to the comment text (`"body"`):

*   **Remove quotes:** Removes quotations from comments.
*   **Remove URLs:**
    *   Plaintext URLs are replaced with `[URL]` (e.g., `http://example.com` → `[URL]`).
    *   Markdown URLs are removed, keeping the link text unless the text itself is also a URL (e.g., `[Example](https://example.com)` → `Example`; `[http://example.com](http://example.com)` → `[URL]`).
*   **Remove inline formatting:**
    *   **Bold:** Double asterisks `**` are removed, the text remains (e.g., `**Text**` → `Text`).
    *   *Italic:* Single asterisks `*` are removed, the text remains (e.g., `*Text*` → `Text`).
    *   ~~Strikethrough~~: Tildes `~~` and the strikethrough text are removed (e.g., `~~Text~~` → *(empty)*).
*   **Remove Zero-Width Spaces:** All Zero-Width Spaces (`\u200B`, `​`, `&#x200B;`) are removed.
*   **Reduce Multiple Newlines:** Consecutive newlines are reduced to a single newline.
*   **Discard Empty Comments:** Comments that are empty or consist only of whitespace after all modifications are not processed further.

All filtering and modifications (except inline formatting) are documented in a log file `filtered_log_{input_filename}.txt`. Since a comment can meet multiple filter criteria (e.g., contain a quote and a URL), a comment may appear multiple times in the log file if multiple filter actions were applied.


### 2. Extraction to JSON Files

**Scripts:** `comment_tree.py` & `comment_processing.py`

These scripts extract comments from filtered `.zst` files and store them in JSON format. The type of storage varies depending on the selected processing mode:

**Grouped Mode (default):**

*   Comments are grouped into threads based on the `link_id`.
*   All comments of a thread are stored in a single JSON file as a list of JSON objects.
*   Filename: `{link_id}_flat.json` (e.g., `10ax890_flat.json`).
*   The original tree structure of comments within the thread is **not** preserved; the comments are stored as a flat list.

**No-Group Mode (`--no-group`):**

*   Each comment is processed individually and stored in a separate JSON file.
*   Each JSON file contains a single JSON object (the comment).
*   Filename: `{link_id}_{comment_id}.json` (e.g., `10wugax_jepcf1r.json`).


### 3. Conversion to XML

**Script:** `json2xml.py`

This script converts the JSON files into TEI-XML format. The XML structure depends on the processing mode:

**Grouped Mode (default):**

*   Creates one XML file per thread.
*   **TEI Header:** Contains metadata about the thread (title, subreddit, date of last comment, thread URL), extracted from the first comment in the JSON file.
*   **XML Body:**
    *   Comments are grouped in a `<list>` element within a `<div type="comments">`.
    *   Each comment is represented as an `<item>` element within the `<list>`.
    *   `<item>` elements contain:
        *   Comment text
        *   `<date>` (creation date)
        *   `<name>` (author)
        *   `source` attribute (comment URL)
        *   Line breaks in the comment text are encoded as `<lb/>`.

**No-Group Mode (`--no-group`):**

*   Creates one XML file per comment.
*   **TEI Header:** Contains more detailed metadata about the comment and thread (title of the thread, subreddit, date of the comment, thread and comment URLs).
*   **XML Body:**
    *   Each comment is placed as a single `<p>` element directly in the `<body>`.
    *   The `<p>` element contains the comment text. No `<item>`, `<list>`, `<date>`, or `<name>` elements in the comment body.
    *   Line breaks in the comment text are encoded as `<lb/>`.

The script `validate.py` is used to check the validity of the XML files.


### Installation

To set up the environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Usage

To run the main script, use:
```bash
python run.py path/to/subreddit.zst
# or to process (and save) each comment individually
python run.py --no-group path/to/subreddit.zst
```

The default mode groups all comments by thread (or "link") in a single JSON and XML file, while the `--no-group` flag saves each comment as a separate JSON and XML file.

### Examples

In the [examples/demo](https://github.com/sgoettel/RedTEI/tree/master/examples/demo) directory, you’ll find sample JSON files in two folders: `grouped` and `ungrouped`. To see the conversion process, run:

```bash
python -m extractor.json2xml
```

The JSON samples will be processed and converted into XML files in their respective folders (`grouped` or `ungrouped`).

### Testing

Run tests with ``pytest``.

For [coverage](https://coverage.readthedocs.io/en/7.4.4/) analysis (currently 80%) use:

```bash
coverage run -m pytest
coverage report -m --include="extractor/*"
```

### Output Directory Structure

After successful execution of the pipeline, the generated JSON and XML files are stored in the following directory structure:

```
subreddits/
└── <subreddit>_<mode>/
    ├── <subreddit>_json_<mode>/
    │   ├── 00001/
    │   │   ├── ...JSON files...
    │   ├── 00002/
    │   │   ├── ...JSON files...
    │   └── ...
    └── <subreddit>_xml_<mode>/
        ├── 00001/
        │   ├── ...XML files...
        ├── 00002/
        │   ├── ...XML files...
        └── ...
```

The JSON and XML files are stored in numbered subdirectories within the respective `_json_...` and `_xml_...` directories.
