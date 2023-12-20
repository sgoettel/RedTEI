import argparse
import os
import sys

from comment_tree import extract_comments
from json2xml import json2xml, run
from trim_user_comments import filter_comments
from validate import validate_directory


def pipeline(zstfile, subreddit, bots=["AutoModerator", "ClausKlebot", "RemindMeBot", "sneakpeekbot", "LimbRetrieval-Bot"]):
    # create general subreddits directory
    if not os.path.exists(f'../subreddits/'):
        os.mkdir(f'../subreddits/')
    # create directory and initialize subdirectory names
    if not os.path.exists(f'../subreddits/{subreddit}'):
        os.mkdir(f'../subreddits/{subreddit}')
    zst_filtered = f"{zstfile.rsplit('.', 1)[0]}_filtered.zst"
    dir_json = f'../subreddits/{subreddit}/{subreddit}_json/'
    dir_xml = f'../subreddits/{subreddit}/{subreddit}_xml/'
    # filter removed comments and bots
    # python trim_username_comments.py -a "AutoModerator" -a "ClausKlebot" -a "RemindMeBot" -a "sneakpeekbot" -a "LimbRetrieval-Bot" -rd wohnen_comments.zst
    # filter_comments(zstfile, bots, True)
    botstr = '" -a "'.join(bots)
    os.system(f'python trim_username_comments.py -a "{botstr}" -rd {zst_file}')
    # extract flat json files
    # python comment_tree.py -a -f wohnen_comments_filtered.zst
    os.system(f'python comment_tree.py -a -f {zst_filtered} {dir_json}')
    print('Convert json to XML files.')
    # convert all json to XML
    run(dir_json, dir_xml)
    print('Validate XMl files.')
    # validate all XML files
    validate_directory(dir_xml)

"""
def argparser():
    # Command line arguments
    parser = argparse.ArgumentParser(description='Tools for creating the data behind `map.html`')
    parser.add_argument('--headers2geojson', action='store_true', help='Create a geoJSON file from DTA-headers')
    parser.add_argument('--headers2geojson_noidmap', action='store_true', help='Create a geoJSON file from DTA-headers (without an id2place mapping file)')
    parser.add_argument('--unifyjson', action='store_true', help='Clean the data in the geoJSON file')
    parser.add_argument('--place2id', action='store_true', help='Create a table from geoJSON file')
    parser.add_argument('--json2kml', action='store_true', help='Create a KML file based on geoJSON file')
    # file path to subreddit zstd
    parser.add_argument('--logfile', default='./log/geofy.log', help='File path to a log file.')
    parser.add_argument('--tsvfile', default='./tsv/dta-geo.tsv', help='File path to a tsv file.')
    parser.add_argument('--tsvfileedit', default='./tsv/dta-geo.YB.tsv', help='File path to a manually edited tsv file.')
    parser.add_argument('--jsonfileraw', default='./json/dta-geo-raw.json', help='File path to a raw json file.')
    parser.add_argument('--jsonfile', default='./json/dta-geo.json', help='File path to a unified json file.')
    parser.add_argument('--kmlfile', default='./kml/dta-geo.kml', help='File path to a kml file.')
    parser.add_argument('--pathheaders', default='./dta-headers/*.xml', help='Path to a directory containing DTA headers in xml files.')

    # Print help and exit if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # Parse arguments
    args = parser.parse_args()

    return args
"""


if __name__ == '__main__':
    zst_file = sys.argv[1]
    subreddit = zst_file.replace('_comments.zst', '')
    pipeline(zst_file, subreddit)