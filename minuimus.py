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

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

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
        except Exception as e:
            logger.exception(f"Error compressing file: {file}. {e}")


class FileProcessor:
    def __init__(
        self, processed_files_file, total_original_size, total_compressed_size
    ):
        self.processed_files_file = processed_files_file
        self.total_original_size = total_original_size
        self.total_compressed_size = total_compressed_size
        self.file_compressor = FileCompressor()

    def process_file(self, file):
        try:
            with open(self.processed_files_file, "rb") as f:
                processed_files = pickle.load(f)
            if file in processed_files:
                logger.info(f"Skipping file: {file}. Already processed.")
                return
            original_size = os.path.getsize(file)
            self.file_compressor.compress_file(file)
            compressed_size = os.path.getsize(file)
            self.total_original_size.value += original_size
            self.total_compressed_size.value += compressed_size
            processed_files.append(file)
            with open(self.processed_files_file, "wb") as f:
                pickle.dump(processed_files, f)
        except Exception as e:
            logger.exception(f"Error processing file: {file}. {e}")


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
            files = f.read().splitlines()
        return files


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
        tqdm.write(f"\nCompression summary:")
        tqdm.write(f"Number of files compressed: {num_files}")
        tqdm.write(f"Total original size: {original_size_str}")
        tqdm.write(f"Total compressed size: {compressed_size_str}")
        tqdm.write(
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

    files = []
    if args.files:
        for arg in args.files:
            if os.path.isfile(arg):
                files.append(arg)
            elif os.path.isdir(arg):
                directory_scanner = DirectoryScanner()
                files.extend(directory_scanner.get_files_from_directory(arg))
            else:
                file_list_reader = FileListReader()
                files.extend(file_list_reader.get_files_from_filelist(arg))

    if args.filelist:
        file_list_reader = FileListReader()
        file_list = os.path.abspath(args.filelist[0])
        if os.path.isfile(file_list):
            files.extend(file_list_reader.get_files_from_filelist(file_list))

    if not os.path.isfile(args.processed_files_file):
        processed_files = []
    else:
        with open(args.processed_files_file, "rb") as f:
            processed_files = pickle.load(f)

    total_original_size = multiprocessing.Manager().Value("i", 0)
    total_compressed_size = multiprocessing.Manager().Value("i", 0)

    file_processor = FileProcessor(
        args.processed_files_file, total_original_size, total_compressed_size
    )

    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = [executor.submit(file_processor.process_file, file) for file in files]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing files"
        ):
            pass

    with open(args.processed_files_file, "wb") as f:
        pickle.dump(processed_files, f)

    compression_summary = CompressionSummary()
    compression_summary.display_summary(
        files, total_original_size, total_compressed_size
    )

if __name__ == "__main__":
    main()