import contextlib
import os
import sys
import subprocess
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from humanize import naturalsize
import pickle
import argparse
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(level=logging.ERROR)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler('minuimus.log', maxBytes=1024*1024, backupCount=10)
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

class FileCompressor:
    def compress_file(self, file):
        try:
            subprocess.run(
                ["perl", "minuimus.pl", file],
                check=True,
                creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS,
            )
        except subprocess.CalledProcessError as e:
            logger.exception(f"Error compressing file: {file}. {e}")
            raise
        except FileNotFoundError as e:
            logger.exception(f"minuimus.pl not found. {e}")
            raise
        except Exception as e:
            logger.exception(f"Error compressing file: {file}. {e}")
            raise


class DirectoryScanner:
    def get_files_from_directory(self, directory):
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        return files


class FileListReader:
    def get_files_from_filelist(self, filelist):
        with open(filelist) as f:
            lines = f.read().splitlines()
        files = []
        directory_scanner = DirectoryScanner()
        for line in lines:
            if os.path.isfile(line):
                files.append(line)
            elif os.path.isdir(line):
                files.extend(directory_scanner.get_files_from_directory(line))
        return files


def get_files(args_files, file_list=None):
    files = []
    directory_scanner = DirectoryScanner()
    file_list_reader = FileListReader()
    for arg in args_files:
        if os.path.isfile(arg):
            files.append(arg)
        elif os.path.isdir(arg):
            files.extend(directory_scanner.get_files_from_directory(arg))
        else:
            files.extend(file_list_reader.get_files_from_filelist(arg))
    if file_list:
        if os.path.isfile(file_list):
            files.extend(file_list_reader.get_files_from_filelist(file_list))
    return files


class FileProcessor:
    def __init__(self, total_original_size, total_compressed_size):
        self.total_original_size = total_original_size
        self.total_compressed_size = total_compressed_size
        self.file_compressor = FileCompressor()

    def process_file(self, file, processed_files):
        try:
            if file in processed_files:
                logger.info(f"Skipping file: {file}. Already processed.")
                return
            original_size = os.path.getsize(file)
            self.file_compressor.compress_file(file)
            compressed_size = os.path.getsize(file)
            self.total_original_size.value += original_size
            self.total_compressed_size.value += compressed_size
            processed_files.add(file)
        except Exception as e:
            logger.exception(f"Error processing file: {file}. {e}")


class CompressionSummary:
    def display_summary(self, files, total_original_size, total_compressed_size):
        num_files = len(files)
        total_saved_space = total_original_size.value - total_compressed_size.value
        if total_original_size.value == 0:
            percent_saved_space = 0
        else:
            percent_saved_space = (total_saved_space / total_original_size.value) * 100
        saved_space_str = naturalsize(total_saved_space)
        original_size_str = naturalsize(total_original_size.value)
        compressed_size_str = naturalsize(total_compressed_size.value)
        logger.info(f"\nCompression summary:")
        logger.info(f"Number of files compressed: {num_files}")
        logger.info(f"Total original size: {original_size_str}")
        logger.info(f"Total compressed size: {compressed_size_str}")
        logger.info(
            f"Total saved space: {saved_space_str} ({percent_saved_space:.2f}% compression ratio)"
        )


def main():
    parser = argparse.ArgumentParser(description='Compress files using minuimus.pl', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('files', metavar='FILE', nargs='*',
                        help='files or directories to compress')
    parser.add_argument('--filelist', '-f', metavar='FILE', nargs=1, default=None,
                        help='file containing list of files to compress')
    parser.add_argument('--processed-files-file', '-p', metavar='FILE',
                        default='processed_files.pkl',
                        help='file to store list of processed files')
    args = parser.parse_args()

    files = get_files(args.files, args.filelist)

    if not os.path.isfile(args.processed_files_file):
        processed_files = set()
    else:
        with open(args.processed_files_file, "rb") as f:
            processed_files = set(pickle.load(f))

    total_original_size = multiprocessing.Manager().Value("i", 0)
    total_compressed_size = multiprocessing.Manager().Value("i", 0)

    file_processor = FileProcessor(total_original_size, total_compressed_size)

    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [executor.submit(file_processor.process_file, file, processed_files) for file in files]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing files"
        ):
            pass

    with open(args.processed_files_file, "wb") as f:
        with contextlib.closing(f):
            pickle.dump(list(processed_files), f)

    compression_summary = CompressionSummary()
    compression_summary.display_summary(
        files, total_original_size, total_compressed_size
    )

if __name__ == "__main__":
    main()