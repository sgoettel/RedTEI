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
- fix bug beim Verarbeiten von Subreddit Kochen (wahrscheinlich ist `permalink` bei älteren Threads nicht vorhanden): 
```
Convert json to XML files.
Traceback (most recent call last):
  File "run.py", line 71, in <module>
    pipeline(zst_file, subreddit)
  File "run.py", line 32, in pipeline
    run(dir_json, dir_xml)
  File "/home/koerber/reddit-json2xml/src/json2xml.py", line 240, in run
    json2xml(f'{dir}/{file}', output_dir=output_dir)
  File "/home/koerber/reddit-json2xml/src/json2xml.py", line 138, in json2xml
    info['permalink'].split('/')
KeyError: 'permalink'
```

Optional:
- original date aus zst und epoch_time