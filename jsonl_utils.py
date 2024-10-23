from typing import *
import jsonlines
import json
import gzip
import os
import os.path as osp


def read_jsonl(path: str) -> List[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File `{path}` does not exist.")
    elif not path.endswith(".jsonl"):
        raise ValueError(f"File `{path}` is not a jsonl file.")
    with jsonlines.open(path) as reader:
        items = [item for item in reader]
    return items


def read_jsonl_map(path: str) -> List[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File `{path}` does not exist.")
    elif not path.endswith(".jsonl"):
        raise ValueError(f"File `{path}` is not a jsonl file.")
    items = {}
    with jsonlines.open(path) as reader:
        for item in reader:
            items[item["task_id"]] = item
    return items


def write_jsonl(path: str, data: List[dict], append: bool = False):
    with jsonlines.open(path, mode="a" if append else "w") as writer:
        for item in data:
            writer.write(item)


def read_jsonl_gz(path: str) -> List[dict]:
    if not path.endswith(".jsonl.gz"):
        raise ValueError(f"File `{path}` is not a jsonl.gz file.")
    with gzip.open(path, "rt") as f:
        data = [json.loads(line) for line in f]
    return data


def json2jsonl(json_path: str, jsonl_path: str):
    with open(json_path, "r") as f:
        data = json.load(f)
    write_jsonl(jsonl_path, data)

# enumerate dataset and resume from output_path if it exists
def enumerate_resume(
    dataset: List[dict],
    output_path: str,
    identifier_key: str = "task_id",
):
    if not os.path.exists(output_path):
        for i, item in enumerate(dataset):
            yield i, item
    else:
        exist_items = []
        with jsonlines.open(output_path) as reader:
            for item in reader:
                exist_items.append(item[identifier_key])

        for i, item in enumerate(dataset):
            # skip items that have been processed before
            if item[identifier_key] in exist_items:
                continue
            yield i, item

import concurrent.futures
from tqdm import tqdm

def read_all_jsonl_files(input_paths, n_workers: int = 8):
    all_data = []

    # Create a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        # Submit reading tasks for all input files
        future_to_file = {executor.submit(read_jsonl, input_path): input_path for input_path in input_paths}

        # Use tqdm to show progress
        for future in tqdm(concurrent.futures.as_completed(future_to_file), total=len(input_paths), desc="Reading files"):
            file_path = future_to_file[future]
            try:
                data = future.result()
                all_data.extend(data)
            except Exception as exc:
                print(f'{file_path} generated an exception: {exc}')

    print(f"Total number of entries in the dataset: {len(all_data)}")
    return all_data
