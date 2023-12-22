# reddit-json2xml

Hilfsskripte zur Verarbeitung von Reddit-Daten und Umwandlung von json in TEI-XML.

## Nutzung
Hauptskript [run.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/run.py): `python src/run.py path-to-subreddit-zsta`

Weitere Skripte:
- [comment_tree.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/comment_tree.py)
- [json2xml.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/json2xml.py): wandelt json-Dateien in Baumstruktur in TEI-valide xml-Dateien um
- [trim_username_comments.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/trim_username_comments.py)
- [validate.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/validate.py): validiere XML-Dateien, nach TEI-Schema

## Beispiele
Einige Beispieldateien für den Subreddit "wohnen" sind im Ordner [examples/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples):
- [wohnen_json/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_json) enthält json-Dateien, die mit `comment_tree.py` aus der Datei `wohnen_comments.zst` extrahiert und mit `trim_username_comments.py -a "AutoModerator" -a "ClausKlebot" -a "RemindMeBot" -a "sneakpeekbot" -a "LimbRetrieval-Bot" -rd wohnen_comments.zst` gefiltert wurden
- [wohnen_xml/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_xml) enthält XML-Dateien, die mit `json2xml.py` aus [wohnen_json/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples/wohnen_json) umgewandelt wurden


## Installation
Virtual Environment erstellen:
```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

## TODO's

- run für weitere Subreddits (bisher: wohnen, Kochen, GermanRap)
- Output Files genauer ansehen
- Bedienbarkeit von `run.py` verbessern (Argparser mit mehr Argumenten)
- logging einbauen
- Funktionen aus `comment_tree.py` und `trim_username_comments.py` in `run.py` importieren statt `os.system`-Aufrufe

Optional:
- original date aus zst und epoch_time