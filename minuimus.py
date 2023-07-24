import os
import sys
import subprocess
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from humanize import naturalsize
import pickle

logging.basicConfig(level=logging.ERROR)

def process_file(file, processed_files_file, total_original_size, total_compressed_size):
    try:
        with open(processed_files_file, "rb") as f:
            processed_files = pickle.load(f)
        if file in processed_files:
            logging.info(f"Skipping file: {file}. Already processed.")
            return
        original_size = os.path.getsize(file)
        subprocess.run(
            ["perl", "minuimus.pl", file],
            check=True,
            # creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS,
        )
        compressed_size = os.path.getsize(file)
        total_original_size.value += original_size
        total_compressed_size.value += compressed_size
        processed_files.append(file)
        with open(processed_files_file, "wb") as f:
            pickle.dump(processed_files, f)
    except subprocess.CalledProcessError as e:
        logging.exception(f"Error processing file: {file}. {e}")
    except Exception as e:
        logging.exception(f"Error processing file: {file}. {e}")

def get_files_from_directory(directory):
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def get_files_from_filelist(filelist):
    with open(filelist) as f:
        files = f.read().splitlines()
    return files

def get_files_from_args(args):
    files = []
    for arg in args:
        if os.path.isfile(arg):
            files.append(arg)
        elif os.path.isdir(arg):
            files.extend(get_files_from_directory(arg))
        else:
            files.extend(get_files_from_filelist(arg))
    return files

def display_summary(files, total_original_size, total_compressed_size):
    num_files = len(files)
    total_saved_space = total_original_size.value - total_compressed_size.value
    if total_original_size.value == 0:
        percent_saved_space = 0
    else:
        percent_saved_space = (total_saved_space / total_original_size.value) * 100
    saved_space_str = naturalsize(total_saved_space)
    original_size_str = naturalsize(total_original_size.value)
    compressed_size_str = naturalsize(total_compressed_size.value)
    print(f"\nCompression summary:")
    print(f"Number of files compressed: {num_files}")
    print(f"Total original size: {original_size_str}")
    print(f"Total compressed size: {compressed_size_str}")
    print(
        f"Total saved space: {saved_space_str} ({percent_saved_space:.2f}% compression ratio)"
    )

if __name__ == "__main__":
    files = get_files_from_args(sys.argv[1:])
    processed_files_file = "processed_files.pkl"
    if os.path.exists(processed_files_file):
        with open(processed_files_file, "rb") as f:
            processed_files = pickle.load(f)
    else:
        processed_files = []
    total_original_size = multiprocessing.Manager().Value('i', 0)
    total_compressed_size = multiprocessing.Manager().Value('i', 0)
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [
            executor.submit(process_file, file, processed_files_file, total_original_size, total_compressed_size) for file in files
        ]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing files"
        ):
            pass

    with open(processed_files_file, "wb") as f:
        pickle.dump(processed_files, f)

    display_summary(files, total_original_size, total_compressed_size)