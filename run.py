import argparse
import json
import os

from multiprocessing import Pool

import zstandard as zstd

from extractor.comment_tree import extract_comments
from extractor.comment_processing import process_comment_batch, process_thread_batch
from extractor.json2xml import json2xml
from extractor.trim_username_comments import process_comments
from extractor.utils import get_output_dir, make_chunks
from extractor.validate import validate_directory


error_log = []  # error log for problematic JSON objects
num_processes = max(os.cpu_count(), 32)


def run_multi_process(func, iterator, chunk_size, json_dir, xml_dir):
    "Run multiprocessing in batches."
    batches = make_chunks(iterator, chunk_size)
    with Pool(processes=num_processes) as pool:
        pool.starmap(
            func,
            [(batch, json_dir, xml_dir) for batch in batches],
        )


def pipeline(zstfile, subreddit, no_group=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    subreddits_dir = os.path.join(base_dir, "subreddits")
    os.makedirs(subreddits_dir, exist_ok=True)

    # define mode based on grouping
    mode = "nogroup" if no_group else "grouped"
    subreddit_folder = os.path.join(subreddits_dir, f"{subreddit}_{mode}")
    os.makedirs(subreddit_folder, exist_ok=True)

    # define JSON and XML output directories based on mode
    json_output_dir = os.path.join(subreddit_folder, f"{subreddit}_json_{mode}")
    xml_output_dir = os.path.join(subreddit_folder, f"{subreddit}_xml_{mode}")

    os.makedirs(json_output_dir, exist_ok=True)
    os.makedirs(xml_output_dir, exist_ok=True)

    # process comments in zst file (apply filters)
    print(f"Filtering comments in {subreddit}...")
    process_comments(
        zstfile,
        remove_deleted=True,
        remove_quotes=True,
        remove_remindme=True,
        remove_urls=True,
    )

    filtered_zst_path = f"{zstfile.rsplit('.', 1)[0]}_filtered.zst"

    print(f"Extracting comments from {filtered_zst_path}. This may take a while...")
    comments = extract_comments(filtered_zst_path)
    print(f"Extracted {len(comments)} comments.")

    # process based on mode
    chunk_size = 100  # batch size
    if no_group:
        unique_comments = {c["id"]: c for c in comments}  # eliminate duplicates
        print(
            f"Processing {len(unique_comments)} unique comments in 'no-group' mode..."
        )
        run_multi_process(
            process_comment_batch,
            unique_comments.values(),
            chunk_size,
            json_output_dir,
            xml_output_dir,
        )
    else:
        thread_comments = {}
        for comment in comments:
            thread_id = comment.get("link_id", "").replace("t3_", "")
            if thread_id not in thread_comments:
                thread_comments[thread_id] = []
            thread_comments[thread_id].append(comment)

        print(f"Processing {len(thread_comments)} threads in 'grouped' mode...")
        run_multi_process(
            process_thread_batch,
            thread_comments.items(),
            chunk_size,
            json_output_dir,
            xml_output_dir,
        )

    print("Validating XML files...")
    validate_directory(xml_output_dir)

    # JSON object count consistency between filtered zst file and JSON output directory
    filtered_zst_path = f"{zstfile.rsplit('.', 1)[0]}_filtered.zst"
    print(
        "Checking consistency of JSON object (comments) count between the filtered .zst file and JSON output directory..."
    )
    compare_json_counts(filtered_zst_path, json_output_dir)


def pipeline_json2xml(dir_json):
    """pipeline if the json files already exist: convert to XML, validate"""
    xml_output_dir = dir_json.replace("json", "xml")
    os.makedirs(xml_output_dir, exist_ok=True)
    for inputfile in os.listdir(dir_json):
        json_path = os.path.join(dir_json, inputfile)
        if os.path.isfile(json_path):
            link_id, comment_id = inputfile.replace(".json", "").split("_")
            # select or create an XML subdirectory for output
            xml_subdir = get_output_dir(xml_output_dir)
            json2xml(
                json_path, output_dir=xml_subdir, link_id=link_id, comment_id=comment_id
            )

    print("Validate XML files.")
    validate_directory(xml_output_dir)


# count JSON objects in a .zst file with NDJSON content
def count_json_objects_in_zst(zst_path):
    count = 0
    with open(zst_path, "rb") as inputfile:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(inputfile) as reader:
            buffer = ""
            while chunk := reader.read(16384):
                buffer += chunk.decode(errors="ignore")
                # count lines in the buffer that correspond to JSON objects
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        count += 1
    return count


# counts JSON objects in all JSON files within a directory
def count_json_objects_in_directory(directory_path):
    count = 0
    for root, _, files in os.walk(directory_path):
        for file_name in files:
            if file_name.endswith(".json"):
                file_path = os.path.join(root, file_name)
                with open(file_path, "r", encoding="utf-8") as inputfile:
                    try:
                        for line in inputfile:
                            json.loads(line)
                            count += 1
                    except json.JSONDecodeError:
                        # handle JSON array format
                        inputfile.seek(0)
                        data = json.load(inputfile)
                        if isinstance(data, list):
                            count += len(data)
    return count


# compare the number of JSON objects in the filtered .zst file and the JSON output directory
def compare_json_counts(filtered_zst_path, json_output_dir):
    zst_count = count_json_objects_in_zst(filtered_zst_path)
    json_count = count_json_objects_in_directory(json_output_dir)

    print(f"Number of JSON objects in filtered .zst file: {zst_count}")
    print(f"Number of JSON objects in JSON output directory: {json_count}")

    if zst_count == json_count:
        print("The number of JSON objects matches.")
    else:
        print(
            "Note: number of JSON objects differ, likely due to comments containing null bytes or control characters that couldn't be processed."
        )
        if error_log:
            print("Details on problematic objects are listed above.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Reddit comments.")
    parser.add_argument(
        "files", nargs="+", help="Path to one or more .zst files or _json directories."
    )
    parser.add_argument(
        "--no-group", action="store_true", help="Process each comment individually."
    )
    args = parser.parse_args()
    for inputfile in args.files:
        if inputfile.endswith(".zst"):
            subreddit = inputfile.split("/")[-1].replace("_comments.zst", "")
            pipeline(inputfile, subreddit, no_group=args.no_group)
        elif inputfile.endswith("_json") or inputfile.endswith("_json/"):
            pipeline_json2xml(inputfile)
        else:
            print(
                "Please provide the path to one or more .zst files or _json directories."
            )
