import os
import sys

from json2xml import run
from validate import load_schema, validate_directory


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
    if not os.path.exists(dir_json):
        os.mkdir(dir_json)
    if not os.path.exists(dir_xml):
        os.mkdir(dir_xml)
    # filter removed comments and bots
    botstr = '" -a "'.join(bots)
    # TODO directly call function, not script
    os.system(f'python trim_username_comments.py -a "{botstr}" -rd {zst_file}')
    # extract flat json files
    #  TODO directly call function, not script
    os.system(f'python comment_tree.py -a -f {zst_filtered} {dir_json}')
    print('Convert json to XML files.')
    # convert all json to XML
    run(dir_json, dir_xml)
    print('Validate XMl files.')
    # validate all XML files
    TEI_RELAXNG = load_schema()
    validate_directory(dir_xml, TEI_RELAXNG)


if __name__ == '__main__':
    # TODO implement argparser
    zst_file = sys.argv[1]
    subreddit = zst_file.split('/')[-1].replace('_comments.zst', '')
    pipeline(zst_file, subreddit)
