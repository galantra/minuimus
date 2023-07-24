import os
import sys
import subprocess
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from humanize import naturalsize

logging.basicConfig(level=logging.INFO)


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

        input_creation_time = os.stat(file).st_ctime
        output_file = f"{file}.min"
        os.utime(output_file, (input_creation_time, input_creation_time))

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
    total_saved_space = total_original_size - total_compressed_size
    if total_original_size == 0:
        percent_saved_space = 0
    else:
        percent_saved_space = (total_saved_space / total_original_size) * 100
    saved_space_str = naturalsize(total_saved_space)
    original_size_str = naturalsize(total_original_size)
    compressed_size_str = naturalsize(total_compressed_size)
    print(f"\nCompression summary:")
    print(f"Number of files compressed: {num_files}")
    print(f"Total original size: {original_size_str}")
    print(f"Total compressed size: {compressed_size_str}")
    print(
        f"Total saved space: {saved_space_str} ({percent_saved_space:.2f}% compression ratio)"
    )


if __name__ == "__main__":
    files = get_files_from_args(sys.argv[1:])
    total_original_size = 0
    total_compressed_size = 0
    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [executor.submit(process_file, file) for file in files]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing files"
        ):
            pass

    display_summary(files, total_original_size, total_compressed_size)
