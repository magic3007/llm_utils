from typing import Callable, List
from multiprocessing import Pool
from tqdm import tqdm
import os.path as osp
import jsonlines
from datetime import datetime
import time
from filelock import FileLock
from llm_utils.jsonl_utils import write_jsonl
from llm_utils.print_utils import make_printv

print_v = make_printv(True)


def enumerate_resume(dataset, output_path, id_key="id"):
    if not osp.exists(output_path):
        for item_id, item in enumerate(dataset):
            yield item_id, item
    else:
        exist_items = []
        with jsonlines.open(output_path) as reader:
            for item in reader:
                exist_items.append(item[id_key])

        for item_id, item in enumerate(dataset):
            # skip items that have been processed before
            if item[id_key] in exist_items:
                continue
            yield item_id, item


def process_item(
    item_id,
    total_items,
    item,
    assemble_func: Callable,
    run_func: Callable,
    process_result_func: Callable,
    output_path: str,
):
    tt = time.time()
    assembled_input = assemble_func(item)
    run_result = run_func(assembled_input)
    processed_result = process_result_func(item, assembled_input, run_result)
    print(f"item_id: {item['id']}, processed_result: {processed_result}")
    if processed_result is not None:
        with FileLock(output_path + ".lock"):
            elapsed = time.time() - tt
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            write_jsonl(output_path, [processed_result], append=True)

    return processed_result


def batch_run(
    dataset: List,
    num_threads: int,
    assemble_func: Callable,
    run_func: Callable,
    process_result_func: Callable,
    output_path: str,
):
    """
    Perform batch processing on a dataset using multiprocessing.

    Args:
    dataset (List): The input dataset to process.
    num_threads (int): Number of threads to use for parallel processing.
    assemble_func (Callable): Function to assemble input for each task.
    run_func (Callable): Function to run for each task.
    process_result_func (Callable): Function to process the result of each task.

    Returns:
    List: Processed results of batch processing.
    """
    total_items = len(dataset)
    resume_dataset = enumerate_resume(dataset, output_path)
    if num_threads > 1:
        with Pool(num_threads) as pool:
            results = list(
                tqdm(
                    pool.starmap(
                        process_item,
                        [
                            (
                                item_id,
                                total_items,
                                item,
                                assemble_func,
                                run_func,
                                process_result_func,
                                output_path,
                            )
                            for item_id, item in resume_dataset
                        ],
                    ),
                    total=total_items,
                )
            )
    else:
        results = [
            process_item(
                item_id,
                total_items,
                item,
                assemble_func,
                run_func,
                process_result_func,
                output_path,
            )
            for item_id, item in resume_dataset
        ]

    return results
