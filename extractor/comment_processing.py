import json

from .json2xml import json2xml
from .utils import get_output_dir


def process_single_comment(comment, json_output_dir, xml_output_dir):
    """process single comment (--no-group)"""
    try:
        comment_id = comment["id"]
        link_id = comment["link_id"].replace("t3_", "")

        # save JSON
        json_subdir = get_output_dir(json_output_dir)
        json_filename = f"{json_subdir}/{link_id}_{comment_id}.json"
        with open(json_filename, "w", encoding="utf-8") as outfile:
            json.dump([comment], outfile, indent=4)

        # convert JSON to XML
        xml_subdir = get_output_dir(xml_output_dir)
        json2xml(json_filename, output_dir=xml_subdir, link_id=link_id, comment_id=comment_id, group_mode=False)
    except Exception as e:
        print(f"Error processing comment {comment_id}: {e}")


def process_thread(thread_id, comments_list, json_output_dir, xml_output_dir):
    """process a single thread (group)"""
    try:
        # save JSON
        json_subdir = get_output_dir(json_output_dir)
        json_filename = f"{json_subdir}/{thread_id}_flat.json"
        with open(json_filename, "w", encoding="utf-8") as outfile:
            json.dump(comments_list, outfile, indent=4)

        # convert JSON to XML
        xml_subdir = get_output_dir(xml_output_dir)
        json2xml(json_filename, output_dir=xml_subdir, link_id=thread_id, group_mode=True)
    except Exception as e:
        print(f"Error processing thread {thread_id}: {e}")


def process_comment_batch(comment_batch, json_output_dir, xml_output_dir):
    """process a batch of comments, iterate through batch and processes each comment individually"""
    for comment in comment_batch:
        process_single_comment(comment, json_output_dir, xml_output_dir)


def process_thread_batch(thread_batch, json_output_dir, xml_output_dir):
    """process a batch of threads, iterates through each thread in batch"""
    try:
        for thread_id, comments_list in thread_batch:
            process_thread(thread_id, comments_list, json_output_dir, xml_output_dir)
    except Exception as e:
        print(f"Error in process_thread_batch: {e}")
        print(f"Thread batch: {thread_batch}")
