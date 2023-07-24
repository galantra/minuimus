import sys
import os
import subprocess
import pickle
from multiprocessing import Pool, get_context
from tqdm import tqdm

# Define an array to store the folder pathsQA
folders = []

# Get the folder path from the command-line arguments
folder_path = sys.argv[1]

# Define an array to store the file paths
files = []

# Define variables to store the total original size and compressed size
total_original_size = 0
total_compressed_size = 0

# Walk through the folder and its subdirectories
for root, dirs, filenames in os.walk(folder_path):
    for filename in filenames:
        # Only process files with certain extensions
        # if not filename.lower().endswith(
        #     (".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp",
        #     ".docx", ".pptx", ".xlsx", ".odt", ".ods", ".odp", ".epub", ".cbz", ".xps",
        #     ".zip", ".7z", ".gz", ".tgz", ".cab", ".jar", ".woff", ".flac", ".swf", ".stl", ".mp3")
        # ):
        files.append(os.path.join(root, filename))


# Define a function to process a single file
def process_file(file):
    """
    Process a file using the 'minuimus.pl' script with below normal priority.

    Args:
        file (str): The path to the file to be processed.
    """
    try:
        # Get the original size of the file
        original_size = os.path.getsize(file)

        # Create the startupinfo object to modify the process creation flags
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= (
            subprocess.STARTF_USESHOWWINDOW
        )  # Hide the console window
        startupinfo.dwFlags |= (
            subprocess.CREATE_NEW_CONSOLE
        )  # Create a new console window for each subprocess

        # Launch the subprocess with below normal priority
        subprocess.run(
            ["perl", "minuimus.pl", file],
            check=True,
            startupinfo=startupinfo,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS,
        )

        # Get the compressed size of the file
        compressed_size = os.path.getsize(file)

        # Update the total original size and compressed size
        global total_original_size, total_compressed_size
        total_original_size += original_size
        total_compressed_size += compressed_size

    except subprocess.CalledProcessError as e:
        print(f"Error processing file: {file}. {e}")
        # Handle the error here, if needed


# Process each file in the files list
for file in tqdm(files, desc="Processing files"):
    process_file(file)


def update_progress_bar(progress, total, bar_length=40):
    percent = float(progress) / total
    filled_length = int(bar_length * percent)
    bar = "=" * filled_length + "-" * (bar_length - filled_length)
    return f"[{bar}] {int(percent * 100)}%"


if __name__ == "__main__":
    TOTAL_FILES = len(files)
    with Pool(os.cpu_count()) as p:  # Use all available cores
        for i, _ in enumerate(p.imap_unordered(process_file, files), 1):
            # Check if the user wants to pause
            if os.path.exists("pause.pickle"):
                p.close()  # Pause the Pool
                p.join()
                print("Script paused. Press 'Enter' to resume.")
                input()
                os.remove("pause.pickle")  # Remove the pause file
                p = Pool(os.cpu_count())  # Resume the Pool

        progress_bar = update_progress_bar(i, TOTAL_FILES)
        print(f"\r{progress_bar}", end="")  # Update progress bar in-place

        # Save the progress
        progress = {
            "files": files,
            "total_files": TOTAL_FILES,
            "current_file_index": i,
        }
        with open("progress.pickle", "wb") as f:
            pickle.dump(progress, f)

    # Calculate the total saved space
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
