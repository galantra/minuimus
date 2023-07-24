import sys
import os
import subprocess
from multiprocessing import Pool
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

with Pool(os.cpu_count()) as p:
    p.map(process_file, files)

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