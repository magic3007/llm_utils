from typing import List, Callable
from multiprocessing import Pool
from tqdm import tqdm


def batch_run(
    dataset: List,
    num_threads: int,
    assemble_func: Callable,
    run_func: Callable,
    process_result_func: Callable,
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

    def process_item(item):
        assembled_input = assemble_func(item)
        run_result = run_func(assembled_input)
        return process_result_func(run_result)

    with Pool(num_threads) as pool:
        results = list(tqdm(pool.imap(process_item, dataset), total=len(dataset)))

    return results
