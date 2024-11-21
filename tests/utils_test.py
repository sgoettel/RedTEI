import os
import tempfile

import zstandard as zstd

from extractor.utils import (
    MAX_FILES_PER_DIR,
    compare_json_counts,
    count_json_objects_in_directory,
    count_json_objects_in_zst,
    get_output_dir,
    make_chunks,
)


def test_chunks():
    assert list(make_chunks([], 2)) == []
    assert list(make_chunks([1], 2)) == [(1,)]
    assert list(make_chunks([1, 2, 3, 4, 5], 2)) == [(1, 2), (3, 4), (5,)]


def test_count_in_file():
    with tempfile.NamedTemporaryFile(suffix=".zst") as tmp:
        assert count_json_objects_in_zst(tmp.name) == 0

    with tempfile.NamedTemporaryFile(suffix=".zst") as tmp:
        with open(tmp.name, "wb") as f:
            f.write(zstd.compress(b'{"key": "value"}\n{"key": "value"}\n'))
        assert count_json_objects_in_zst(tmp.name) == 2


def test_count_in_dir():
    with tempfile.TemporaryDirectory() as tmp:
        # valid file
        file_path = os.path.join(tmp, "file.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('{"key": "value"}\n{"key": "value"}\n')
        # invalid file
        file_path = os.path.join(tmp, "file.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("test")
        assert count_json_objects_in_directory(tmp) == 2


def test_compare_json_counts():
    payload = '{"key": "value"}\n{"key": "value"}\n'

    with tempfile.TemporaryDirectory() as tmp:
        file_path = os.path.join(tmp, "file.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(payload)

        zst_path = os.path.join(tmp, "file.zst")
        with open(zst_path, "wb") as f:
            f.write(zstd.compress(payload.encode("utf-8")))

        zst_count = count_json_objects_in_zst(zst_path)
        json_count = count_json_objects_in_directory(tmp)
        assert zst_count == json_count

        # run the function
        compare_json_counts(zst_path, tmp)


def test_output_dir():
    with tempfile.TemporaryDirectory() as tmp:

        output_dir = get_output_dir(tmp)
        assert os.path.exists(output_dir) and os.path.isdir(output_dir)
        assert output_dir == os.path.join(tmp, "00001")

        for i in range(MAX_FILES_PER_DIR):
            file_path = os.path.join(output_dir, f"file_{i}.txt")
            with open(file_path, "wb") as f:
                f.write(b"test")

        new_output_dir = get_output_dir(tmp)
        assert new_output_dir != output_dir
        assert os.path.exists(new_output_dir) and os.path.isdir(new_output_dir)
        assert new_output_dir == os.path.join(tmp, "00002")
