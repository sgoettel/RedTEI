"""
Extract comments from a Reddit zst file

Author: Sebastian Göttel, 2023, script based on:
https://github.com/sgoettel/zstsidescripts/blob/main/comment_tree.py
"""

import json
import zstandard as zstd

CHUNK_SIZE = 16384

UNWANTED_FIELDS = [
    "all_awardings",
    "approved_at_utc",
    "approved_by",
    "archived",
    "associated_award",
    "author_created_utc",
    "author_flair_background_color",
    "author_flair_css_class",
    "author_flair_richtext",
    "author_flair_template_id",
    "author_flair_text",
    "author_flair_text_color",
    "author_flair_type",
    "author_fullname",
    "author_is_blocked",
    "author_patreon_flair",
    "author_premium",
    "awarders",
    "banned_at_utc",
    "banned_by",
    "can_gild",
    "can_mod_post",
    "collapsed",
    "collapsed_because_crowd_control",
    "collapsed_reason",
    "collapsed_reason_code",
    "comment_type",
    "controversiality",
    "created",
    "distinguished",
    "downs",
    "editable",
    "edited",
    "gilded",
    "gildings",
    "is_submitter",
    "likes",
    "locked",
    "_meta",
    "mod_note",
    "mod_reason_by",
    "mod_reason_title",
    "mod_reports",
    "name",
    "no_follow",
    "num_reports",
    "parent_id",
    "quarantined" "removal_reason",
    "removal_reason",
    "replies",
    "report_reasons",
    "saved",
    "score",
    "score_hidden",
    "send_replies",
    "stickied",
    "subreddit_id",
    "subreddit_name_prefixed",
    "subreddit_type",
    "top_awarded_type",
    "total_awards_received",
    "treatment_tags",
    "unrepliable_reason",
    "updated_on",
    "ups",
    "user_reports",
]

def prune_object(obj):
    "Delete unwanted keys in dict extracted from JSON."
    for field in UNWANTED_FIELDS:
        if field in obj:
            del obj[field]


def extract_comments(zst_file, link_id=None):
    "Read a ZST file containing comments and extract them."
    dctx = zstd.ZstdDecompressor()
    seen_ids = set()

    with open(zst_file, 'rb') as fh:
        with dctx.stream_reader(fh) as reader:
            bufferstr = ""

            while True:
                chunk = reader.read(CHUNK_SIZE)
                if not chunk:
                    break

                bufferstr += chunk.decode(errors='ignore')

                while True:
                    position = bufferstr.find('\n')
                    if position == -1:
                        break

                    line = bufferstr[:position]
                    bufferstr = bufferstr[position + 1:]

                    try:
                        obj = json.loads(line)

                        if link_id and obj.get('link_id', '').replace('t3_', '') != link_id:
                            continue

                        if obj.get('link_id', '').startswith('t3_'):

                            if obj['id'] not in seen_ids:
                                seen_ids.add(obj['id'])

                                prune_object(obj)
                                yield obj

                    except Exception as e:
                        print(f"Error processing object: {e}. Author: {obj.get('author', 'Unknown Author')}", end="")
                        if 'permalink' in obj:
                            print(f", Permalink: {obj['permalink']}")
                        else:
                            print()
                        continue
