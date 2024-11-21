import json
import os

from collections import defaultdict
from itertools import islice

import zstandard as zstd


error_log = []  # error log for problematic JSON objects
MAX_FILES_PER_DIR = 1000  # max files each folder
directory_state = defaultdict(lambda: {"current_dir": None})


def get_output_dir(base_dir):
    """ensures each directory contains exactly MAX_FILES_PER_DIR files before creating a new one."""
    state = directory_state[base_dir]

    # check if current directory is full or not initialized
    if not state["current_dir"] or len(os.listdir(state["current_dir"])) >= MAX_FILES_PER_DIR:
        # find existing subdirectories
        subdirs = sorted(
            [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.isdigit()],
            key=lambda x: int(x),
        )
        # determine the name for the new directory
        next_subdir = str(int(subdirs[-1]) + 1).zfill(5) if subdirs else "00001"
        new_dir = os.path.join(base_dir, next_subdir)
        os.makedirs(new_dir, exist_ok=True)
        state["current_dir"] = new_dir

    return state["current_dir"]


def make_chunks(iterable, n):
    """split list into n-sized chunks."""
    # 3.12+: https://docs.python.org/3/library/itertools.html#itertools.batched
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        yield batch


def count_json_objects_in_zst(zst_path):
    "Count JSON objects in a .zst file with NDJSON content."
    count = 0
    with open(zst_path, "rb") as inputfile:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(inputfile) as reader:
            bufferstr = ""
            while chunk := reader.read(16384):
                bufferstr += chunk.decode(errors="ignore")
                # count lines in the buffer that correspond to JSON objects
                while "\n" in bufferstr:
                    line, bufferstr = bufferstr.split("\n", 1)
                    if line.strip():
                        count += 1
    return count


def count_json_objects_in_directory(directory_path):
    "Count JSON objects in all JSON files within a directory."
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


def compare_json_counts(filtered_zst_path, json_output_dir):
    "Compare the number of JSON objects in the filtered .zst file and the JSON output directory."
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
