from argparse import ArgumentParser
import os, re
from lib import hashes_db

def process_directory(dirpath: str):
    for root, _, files in os.walk(dirpath):
        for file in files:
            filepath = os.path.join(root, file)
            if not os.path.isfile(filepath):
                print(f"Skipping {filepath} as it is not a file.")
                continue
            hashes_db.add_file_to_db(os.path.basename(dirpath), filepath)
    print(f"Finished processing directory {dirpath}.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Rebuild the hashes database from files in a directory organized by the main script.")
    parser.add_argument("directory", type=str, help="Directory to process")
    args = parser.parse_args()
    dirpath = args.directory
    # Verify if the directory is in the expected format
    if not os.path.exists(dirpath):
        print(f"Directory {dirpath} does not exist.")
        exit(1)
    if not os.path.isdir(dirpath):
        print(f"{dirpath} is not a directory.")
        exit(1)
    # Reset the hashes database to start fresh
    hashes_db.reset_hashes_db()
    for root, dirs, _ in os.walk(dirpath):
        for dir in dirs:
            # Check if the directory name is a year or the special case "Dateless"
            if not re.match(r"^(\d{4}|Dateless)$", dir):
                print(f"Skipping directory {dir} in {root} as it does not match the expected format.")
                continue
            process_directory(os.path.join(root, dir))
    print("Finished rebuilding the hashes database.")
