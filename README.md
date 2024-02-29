# reddit-json2xml

Hilfsskripte zur Verarbeitung von Reddit-Daten und Umwandlung von json in TEI-XML.

## Nutzung
Hauptskript [run.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/run.py): `python src/run.py path/to/subreddit.zst`

Weitere Skripte:
- [comment_tree.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/comment_tree.py): Ordnet alle Kommentare einem Thread zu (Details im Wiki)
- [json2xml.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/json2xml.py): Wandelt json-Dateien in Baumstruktur in TEI-valide XML-Dateien um
- [trim_username_comments.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/trim_username_comments.py): Filtert Kommentare (Details im Wiki)
- [validate.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/validate.py): validiere XML-Dateien, nach TEI-Schema
- [integrity_zst_xml.py](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/src/integrity_zst_xml.py): Überprüft, ob alles korrekt konvertiert wurde: Zählt Kommentare in der (gefilterten) zst-Datei, extrahiert IDs und zählt die <item>-Tags in den XML-Dateien, die denselben IDs entsprechen. `python3 integrity_zst_xml.py path/zst_filtered.zst path/xml/directory `

## Beispiele
Im Ordner [examples/](https://git.zdl.org/koerber/reddit-json2xml/src/branch/master/examples) finden sich drei (verkleinerte) Subreddits. In jedem Ordner liegen die zugrundeliegende zst-Datei (Input für run.py) des jeweiligen Subreddits, die daraus prozessierten JSON- und XML-Dateien (Output) sowie die zugehörige Logdatei.

## Installation
Virtual Environment erstellen:
```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```