# RedTEI

This project provides a pipeline, orchestrated by `run.py`, to transform Reddit comments sourced from the Pushshift archive into TEI-XML format.

**For detailed documentation, including in-depth descriptions of processing steps, data structure, and configuration options, please see the [RedTEI Wiki](https://github.com/sgoettel/RedTEI/wiki/Introduction).**

To set up the environment, make sure you are using **Python 3.12+**:
```bash
python3.12 --version
```
<!-- If python3.12 is not available, install it first:
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
-->

Create and activate the virtual environment:
```bash
python3 -m venv .venv # ensure Python 3.12+ is used
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
