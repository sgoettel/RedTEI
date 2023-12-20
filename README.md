# reddit-json2xml

Hilfsskripte zur Verarbeitung von Reddit-Daten und Umwandlung von json in TEI-XML.

## Nutzung
- [json2xml.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/json2xml.py): wandelt json-Dateien in Baumstruktur in TEI-valide xml-Dateien um
- [validate.ipynb](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/validate.ipynb): validiere XML-Dateien, nach TEI-Schema (Pfad zu `tei-schema-pickle.lzma` im Skript ergänzen)

## Beispiele
Einige Beispieldateien für den Subreddit "wohnen" sind im Ordner [examples/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples):
- [wohnen_trees/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_trees) enthält json-Dateien, die mit `comment_tree.py` aus der Datei `wohnen_comments.zst` extrahiert wurden
- [wohnen_xml/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_xml) enthält XML-Dateien, die mit `json2xml.py` aus [wohnen_trees/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_trees) umgewandelt wurden
- [wohnen_filtered_trees/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_filtered_trees) enthält json-Dateien, die mit `comment_tree.py` aus der Datei `wohnen_comments_filtered.zst` extrahiert und mit `trim_username_comments.py -a "AutoModerator" -a "ClausKlebot" -a "RemindMeBot" -a "sneakpeekbot" -a "LimbRetrieval-Bot" -rd wohnen_comments.zst` gefiltert wurden
- [wohnen_filtered_xml/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_filtered_xml) enthält XML-Dateien, die mit `json2xml.py` aus [wohnen_filtered_trees/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_filtered_trees) umgewandelt wurden

## Installation
Virtual Environment erstellen:
```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

## TODO's
Probleme:
- []

Optional:
- [] original date aus zst und epoch_time