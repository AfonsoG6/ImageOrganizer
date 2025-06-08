from argparse import ArgumentParser
import os, re
from lib import hashes_db

library_path: str
duplicates: list[str] = []

def process_directory(dirpath: str):
    for root, _, files in os.walk(dirpath):
        for file in files:
            filepath = os.path.join(root, file)
            if not os.path.isfile(filepath):
                print(f"Skipping {filepath} as it is not a file.")
                continue
            if hashes_db.exists_identical_file(library_path, filepath, os.path.basename(dirpath)):
                print(f"Skipping {filepath} as an identical file already exists in the database.")
                duplicates.append(filepath)
            else:
                hashes_db.add_file_to_db(library_path, os.path.basename(dirpath), filepath)
    print(f"Finished processing directory {dirpath}.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Rebuild the hashes database from files in a directory organized by the main script.")
    parser.add_argument("directory", type=str, help="Directory to process")
    args = parser.parse_args()
    library_path = args.directory
    # Verify if the directory is in the expected format
    if not os.path.exists(library_path):
        print(f"Directory {library_path} does not exist.")
        exit(1)
    if not os.path.isdir(library_path):
        print(f"{library_path} is not a directory.")
        exit(1)
    # Reset the hashes database to start fresh
    hashes_db.reset_hashes_db(library_path)
    for root, dirs, _ in os.walk(library_path):
        for dir in dirs:
            # Check if the directory name is a year or the special case "Dateless"
            if not re.match(r"^(\d{4}|Dateless)$", dir):
                print(f"Skipping directory {dir} in {root} as it does not match the expected format.")
                continue
            process_directory(os.path.join(root, dir))
    print("Finished rebuilding the hashes database.")
    if len(duplicates) > 0:
        print("The following files were skipped as duplicates:")
        for dup in duplicates:
            print("- " + dup)
        print("Do you want to remove these files? (y/n)")
        response = None
        while response not in ["y", "n"]:
            response = input().strip().lower()
        if response == "y":
            for dup in duplicates:
                try:
                    os.remove(dup)
                    print(f"Removed duplicate file: {dup}")
                except Exception as e:
                    print(f"Failed to remove {dup}: {e}")
    else:
        print("No duplicate files found.")
    print("Done!")