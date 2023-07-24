import os
import sys
import subprocess
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from humanize import naturalsize

logging.basicConfig(level=logging.INFO)

folder_path = sys.argv[1]
files = [entry.path for entry in os.scandir(folder_path) if entry.is_file()]
total_original_size = 0
total_compressed_size = 0

def process_file(file):
    try:
        original_size = os.path.getsize(file)
        subprocess.run(
            ["perl", "minuimus.pl", file],
            check=True,
            # creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS,
        )
        compressed_size = os.path.getsize(file)
        global total_original_size, total_compressed_size
        total_original_size += original_size
        total_compressed_size += compressed_size
    except subprocess.CalledProcessError as e:
        logging.exception(f"Error processing file: {file}. {e}")
    except Exception as e:
        logging.exception(f"Error processing file: {file}. {e}")

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [executor.submit(process_file, file) for file in files]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing files"):
            pass

    total_saved_space = total_original_size - total_compressed_size
    if total_original_size == 0:
        percent_saved_space = 0
    else:
        percent_saved_space = (total_saved_space / total_original_size) * 100
    saved_space_str = naturalsize(total_saved_space)
    logging.info(
        f"\nProcessing complete! Total saved space: {saved_space_str} ({percent_saved_space:.2f}%)."
    )