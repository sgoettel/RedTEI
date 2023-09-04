from datetime import datetime
import json
import os

from lxml.etree import Element, ElementTree, SubElement, fromstring, tostring


def build_subcomments(supercomment_element, subcomment):
    comment = SubElement(supercomment_element, 'comment', id=subcomment['id'], author=subcomment['author'])
    comment.text = subcomment['body']
    if subcomment['responses']:
        for r in subcomment['responses']:
            if r['body'] != '[deleted]' and r['author'] != '[deleted]':
                build_subcomments(comment, r)

def json2xml(file, tree_structure=True, output_dir='wohnen_xml'):
    # read json file
    with open(file, 'r', encoding='latin-1') as f:
        txt = f.read()
    comments = json.loads(txt)
    # extract post metadata information
    docmeta = dict()
    # use first comment entry to extract meta data information
    _, info = list(comments.items())[0]
    time = datetime.utcfromtimestamp(int(info['created_utc']))
    # FRAGE allgemeine Metadaten werden hier aus erstem comment extrahiert
    # woher können wir das Datum vom Ursprungspost ziehen? genauso author?
    docmeta["date"] = str(time.date())
    # permalink example: /r/wohnen/comments/qqro38/wie_soll_ich_mit_meinen_überempfindlichen/hk1xuv3/
    _, _, subreddit, _, post_id, title, comment_id, _ = info['permalink'].split('/')
    # FRAGE _ ersetzen? casing rekonstruieren?
    docmeta["title"] = title
    docmeta["url"] = f'https://www.reddit.com/r/{subreddit}/comments/{post_id}/{title}/'
    docmeta["subreddit"] = subreddit

    # build tei xml doc
    teidoc = Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    header = SubElement(teidoc, 'teiHeader')
    filedesc = SubElement(header, 'fileDesc')
    sourcedesc = SubElement(filedesc, 'sourceDesc')
    source_bibl = SubElement(sourcedesc, 'bibl')

    # FRAGE wo subreddit?
    bib_titlestmt = SubElement(filedesc, 'titleStmt')
    bib_titlemain = SubElement(bib_titlestmt, 'title', type='main')
    bib_titlemain.text = docmeta["title"]
    if 'author' in docmeta.keys():
        bib_author = SubElement(bib_titlestmt, 'author')
        bib_author.text = docmeta.author

    biblfull = SubElement(sourcedesc, 'biblFull')
    publicationstmt = SubElement(filedesc, 'publicationStmt')
    # FRAGE subreddit unter publisher?
    publication_date = SubElement(publicationstmt, 'date')
    publication_date.text = docmeta['date']
    publication_url = SubElement(publicationstmt, 'ptr', type='URL', target=docmeta['url'])

    text = SubElement(teidoc, "text")
    body = SubElement(text, "body")
    # correct level for responses? or rather under text or other?
    responses = SubElement(text, "comments")
    # iterate comments to include responses
    for id, comment in comments.items():
        if comment['body'] != '[deleted]' and comment['author'] != '[deleted]':
            # FRAGE sollen subcomments von gelöschten comments trotzdem gelistet werden?
            # auf reddit steht nur [gelöscht] und keine subcomments mehr
            build_subcomments(responses, comment)
                       
    tei_str = tostring(teidoc, pretty_print=True, encoding='utf-8').decode('utf-8')
    if output_dir:
        ElementTree(teidoc).write(f'{output_dir}/{post_id}.xml', pretty_print=True, encoding='utf-8')
    return tei_str

def demo():
    print(json2xml('wohnen_trees/qqro38_tree.json'))

def run(dir='wohnen_trees'):
    for file in os.listdir(dir)[:100]:
        json2xml(f'{dir}/{file}')

if __name__ == '__main__':
    demo()
    # run()
