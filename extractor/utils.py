import os
from collections import defaultdict

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
