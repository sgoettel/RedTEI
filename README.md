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

## Citation

If you use this work, please refer to: 
```
@misc{goettel2025redtei,
    title = {{Reddit als (Text-)Ressource: Erstellung und Nachnutzbarkeit eines deutschsprachigen Reddit-Korpus.}},
    author = {G{\"o}ttel, Sebastian, and K{\"o}rber, Lydia, and Barbaresi, Adrien},
    type = {Poster},
    month = mar,
    year = "2025",
    url = "https://zenodo.org/records/14944553",
    doi = "10.5281/zenodo.14944553",
    note = {Poster presented at DHd 2025 Under Construction (DHd2025)}
}
```

## License

This repository is licensed under the [GNU General Public License v3.0GNU General Public License v3.0](https://github.com/sgoettel/RedTEI/blob/master/LICENSE).
