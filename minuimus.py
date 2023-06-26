import os
import subprocess
import pickle
from multiprocessing import Pool, get_context
from tqdm import tqdm

# Define an array to store the folder paths
folders = [
    # r"C:\Users\emanresu\AppData\Roaming\Anki2\Jura",
    r"C:\Users\emanresu\Documents\Calibre Libraries",
    # r"C:\Users\emanresu\AppData\Roaming\Anki2\Alg",
    # r"C:\Users\emanresu\AppData\Roaming\Anki2\ES",
    # r"C:\Users\emanresu\AppData\Roaming\Anki2\EN"
]

def process_file(file):
    """
    Process a file using the 'minuimus.pl' script with below normal priority.
    
    Args:
        file (str): The path to the file to be processed.
    """
    try:
        # Create the startupinfo object to modify the process creation flags
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # Hide the console window
        startupinfo.dwFlags |= subprocess.CREATE_NEW_CONSOLE  # Create a new console window for each subprocess

        # Launch the subprocess with below normal priority
        subprocess.run(["perl", r"C:\Users\emanresu\PortableApps\minuimus\minuimus.pl", file],
                       check=True, startupinfo=startupinfo, creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    except subprocess.CalledProcessError as e:
        print(f"Error processing file: {file}. {e}")
        # Handle the error here, if needed

def update_progress_bar(progress, total, bar_length=40):
    percent = float(progress) / total
    filled_length = int(bar_length * percent)
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    return f"[{bar}] {int(percent * 100)}%"

if __name__ == '__main__':
    files = []
    for folder in folders:
        for root, dirs, files_list in os.walk(folder):
            for filename in files_list:
                if not filename.endswith(".mp3"):
                    file_path = os.path.join(root, filename)
                    files.append(file_path)

    TOTAL_FILES = len(files)
    with Pool(12) as p:
        for i, _ in enumerate(p.imap_unordered(process_file, files), 1):
            # Check if the user wants to pause
            if os.path.exists("pause.pickle"):
                p.close()  # Pause the Pool
                p.join()
                print("Script paused. Press 'Enter' to resume.")
                input()
                os.remove("pause.pickle")  # Remove the pause file
                p = Pool(12)  # Create a new Pool

            progress_bar = update_progress_bar(i, TOTAL_FILES)
            print(f"\r{progress_bar}", end="")  # Update progress bar in-place

            # Save the progress
            progress = {
                "files": files,
                "total_files": TOTAL_FILES,
                "current_file_index": i
            }
            with open("progress.pickle", "wb") as f:
                pickle.dump(progress, f)

    print("\nProcessing complete!")
