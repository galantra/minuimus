import sys
import os
import subprocess
import pickle
from multiprocessing import Pool, get_context
from tqdm import tqdm

folders = []
folder_path = sys.argv[1]
files = []
total_original_size = 0
total_compressed_size = 0

for root, dirs, filenames in os.walk(folder_path):
    for filename in filenames:
        files.append(os.path.join(root, filename))

def process_file(file):
    try:
        original_size = os.path.getsize(file)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= (
            subprocess.STARTF_USESHOWWINDOW
        )
        startupinfo.dwFlags |= (
            subprocess.CREATE_NEW_CONSOLE
        )
        subprocess.run(
            ["perl", "minuimus.pl", file],
            check=True,
            startupinfo=startupinfo,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS,
        )
        compressed_size = os.path.getsize(file)
        global total_original_size, total_compressed_size
        total_original_size += original_size
        total_compressed_size += compressed_size
    except subprocess.CalledProcessError as e:
        print(f"Error processing file: {file}. {e}")

for file in tqdm(files, desc="Processing files"):
    process_file(file)

def update_progress_bar(progress, total, bar_length=40):
    percent = float(progress) / total
    filled_length = int(bar_length * percent)
    bar = "=" * filled_length + "-" * (bar_length - filled_length)
    return f"[{bar}] {int(percent * 100)}%"

if __name__ == "__main__":
    TOTAL_FILES = len(files)
    with Pool(os.cpu_count()) as p:
        for i, _ in enumerate(p.imap_unordered(process_file, files), 1):
            if os.path.exists("pause.pickle"):
                p.close()
                p.join()
                print("Script paused. Press 'Enter' to resume.")
                input()
                os.remove("pause.pickle")
                p = Pool(os.cpu_count())
        progress_bar = update_progress_bar(i, TOTAL_FILES)
        print(f"\r{progress_bar}", end="")
        progress = {
            "files": files,
            "total_files": TOTAL_FILES,
            "current_file_index": i,
        }
        with open("progress.pickle", "wb") as f:
            pickle.dump(progress, f)
    total_saved_space = total_original_size - total_compressed_size
    percent_saved_space = (total_saved_space / total_original_size) * 100
    if total_saved_space < 1024:
        saved_space_unit = "bytes"
    elif total_saved_space < 1048576:
        saved_space_unit = "KB"
        total_saved_space /= 1024
    elif total_saved_space < 1073741824:
        saved_space_unit = "MB"
        total_saved_space /= 1048576
    else:
        saved_space_unit = "GB"
        total_saved_space /= 1073741824
    print(
        f"\nProcessing complete! Total saved space: {total_saved_space:.2f} {saved_space_unit} ({percent_saved_space:.2f}%)."
    )