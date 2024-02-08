import os
import sys

from json2xml import run
from validate import load_schema, validate_directory

# read botlist from file
def read_bot_list(file_path):
    with open(file_path, 'r') as file:
        # Add doublequotes around each bot name
        bots = ['"' + line.strip() + '"' for line in file.readlines() if line.strip()]
    return bots

def pipeline(zstfile, subreddit, config_dir='../src/config/'):
    # path to botlist
    bot_file_path = os.path.join(config_dir, 'botlist.txt')
    bots = read_bot_list(bot_file_path)
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
    botstr = ' -a '.join(bots)
    # TODO directly call function, not script
    os.system(f'python trim_username_comments.py -a {botstr} -rd -rq -rr -ru {zst_file}')
    # extract flat json files
    #  TODO directly call function, not script
    os.system(f'python comment_tree.py -a -f {zst_filtered} {dir_json}')
    print('Convert json to XML files.')
    # convert all json to XML
    run(dir_json, dir_xml)
    print('Validate XML files.')
    # validate all XML files
    TEI_RELAXNG = load_schema()
    validate_directory(dir_xml, TEI_RELAXNG)


if __name__ == '__main__':
    # TODO implement argparser
    zst_file = sys.argv[1]
    subreddit = zst_file.split('/')[-1].replace('_comments.zst', '')
    pipeline(zst_file, subreddit)
