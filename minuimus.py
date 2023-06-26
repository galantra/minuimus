

import os
import subprocess
from multiprocessing import Pool
from tqdm import tqdm

# Define an array to store the folder paths
folders = [
    r"C:\Users\emanresu\Pictures\Interrail Juni 2016",
    r"C:\Users\emanresu\Pictures\Johannes A5",
    r"C:\Users\emanresu\Pictures\Abi 2016",
    r"C:\Users\emanresu\Pictures\Pictures OnePlus 6",
    r"C:\Users\emanresu\Pictures\Mallorca 2019",
    r"C:\Users\emanresu\Pictures\London 2018",
    r"C:\Users\emanresu\Pictures\Selbst",
    r"C:\Users\emanresu\Pictures\Malta 2017"
]

def process_file(file_path):
    """
    Process a file using the 'minuimus.pl' script.
    
    Args:
        file_path (str): The path to the file to be processed.
    """
    subprocess.run(["perl", "minuimus.pl", "--zip-7z", file_path], check=True)

if __name__ == '__main__':
    files = []
    for folder in folders:
        for root, dirs, files_list in os.walk(folder):
            for filename in files_list:
                if filename.endswith(".jpg") or filename.endswith(".png"):
                    files.append(os.path.join(root, filename))

    TOTAL_FILES = len(files)
    with Pool(4) as p:
        with tqdm(total=TOTAL_FILES, desc="Processing Files") as pbar:
            for _ in p.imap_unordered(process_file, files):
                pbar.update(1)
