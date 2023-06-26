import os
import subprocess
import pickle
from multiprocessing import Pool
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
    Process a file using the 'minuimus.pl' script.
    
    Args:
        file (str): The path to the file to be processed.
    """
    try:
        subprocess.run(["perl", r"C:\Users\emanresu\PortableApps\minuimus\minuimus.pl", file], check=True)
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
        with tqdm(total=TOTAL_FILES, desc="Processing Files", ncols=60) as pbar:
            for i, _ in enumerate(p.imap_unordered(process_file, files), 1):
                pbar.set_postfix({"File": f"{i}/{TOTAL_FILES}"})
                pbar.set_description(update_progress_bar(i, TOTAL_FILES))
                pbar.update()

                # Check if the user wants to pause
                if os.path.exists("pause.pickle"):
                    p.close()  # Pause the Pool
                    p.join()
                    print("Script paused. Press 'Enter' to resume.")
                    input()
                    os.remove("pause.pickle")  # Remove the pause file
                    p = Pool(12)  # Create a new Pool
                    pbar = tqdm(total=TOTAL_FILES, desc="Processing Files", ncols=60, initial=i)
                    pbar.set_description(update_progress_bar(i, TOTAL_FILES))
                    pbar.update(i)

                    # Save the progress
                    progress = {
                        "files": files,
                        "total_files": TOTAL_FILES,
                        "current_file_index": i
                    }
                    with open("progress.pickle", "wb") as f:
                        pickle.dump(progress, f)

    print("Processing complete!")
