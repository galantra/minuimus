import sys
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pathlib import Path

logging.basicConfig(level=logging.INFO)

folder_path = Path(sys.argv[1])
files = list(folder_path.glob('**/*.*'))
total_original_size = 0
total_compressed_size = 0

def process_file(file):
    try:
        original_size = file.stat().st_size
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= (
            subprocess.STARTF_USESHOWWINDOW
        )
        startupinfo.dwFlags |= (
            subprocess.CREATE_NEW_CONSOLE
        )
        subprocess.run(
            ["perl", "minuimus.pl", str(file)],
            check=True,
            startupinfo=startupinfo,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS,
        )
        compressed_size = file.stat().st_size
        global total_original_size, total_compressed_size
        total_original_size += original_size
        total_compressed_size += compressed_size
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing file: {file}. {e}")
    except Exception as e:
        logging.error(f"Error processing file: {file}. {e}")

with ThreadPoolExecutor() as executor:
    futures = [executor.submit(process_file, file) for file in files]
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing files"):
        pass

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
logging.info(
    f"\nProcessing complete! Total saved space: {total_saved_space:.2f} {saved_space_unit} ({percent_saved_space:.2f}%)."
)