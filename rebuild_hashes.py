from argparse import ArgumentParser
import os, re
from lib import hashes_db
from lib.color import Color

library_path: str
duplicates: list[str] = []

def process_directory(dirpath: str):
    for root, _, files in os.walk(dirpath):
        for file in files:
            filepath = os.path.join(root, file)
            if not os.path.isfile(filepath):
                continue
            if hashes_db.exists_identical_file(filepath, os.path.basename(dirpath)):
                print(Color.color_text(f"[DUP] {os.path.basename(dirpath)}\\{os.path.basename(filepath)}", Color.yellow))
                duplicates.append(filepath)
            else:
                hashes_db.add_file_to_db(os.path.basename(dirpath), filepath)
    print(f"Finished processing directory {dirpath}.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Rebuild the hashes database from files in a directory organized by the main script.")
    parser.add_argument("directory", type=str, help="Directory to process")
    args = parser.parse_args()
    library_path = args.directory
    # Verify if the directory is in the expected format
    if not os.path.exists(library_path):
        print(Color.color_text(f"[!!!] Directory {library_path} does not exist.", Color.red))
        exit(1)
    if not os.path.isdir(library_path):
        print(Color.color_text(f"[!!!] {library_path} is not a directory.", Color.red))
        exit(1)
    # Reset the hashes database to start fresh
    hashes_db.reset_hashes_db(library_path)
    for root, dirs, _ in os.walk(library_path):
        for dir in dirs:
            # Check if the directory name is a year or the special case "Dateless"
            if not re.match(r"^(\d{4}|Dateless)$", dir):
                print(Color.color_text(f"[!!!] Skipping directory {dir} as it does not match the expected format.", Color.yellow))
                continue
            process_directory(os.path.join(root, dir))
    hashes_db.save_hashes_db()
    print(Color.color_text("[iii] Finished rebuilding the hashes database.", Color.lightgrey))
    if len(duplicates) > 0:
        print(Color.color_text("[iii] The following files were skipped as duplicates:", Color.lightgrey))
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
                    print(Color.color_text(f"[iii] Removed duplicate file: {dup}", Color.lightgrey))
                except Exception as e:
                    print(Color.color_text(f"[!!!] Failed to remove {dup}: {e}", Color.yellow))
    else:
        print("No duplicate files found.")
    print("Done!")