import json, os, subprocess

HASHES_DB_FILENAME = "hashes.json"


def load_hashes_db() -> dict[str, list[str]]:
    hashes_db: dict[str, list[str]] = {}
    if os.path.exists(HASHES_DB_FILENAME):
        with open(HASHES_DB_FILENAME, "r") as f:
            hashes_db = json.load(f)
    else:
        hashes_db = {}
    print(f"Loaded hashes database with {len(hashes_db)} entries.")
    return hashes_db


def save_hashes_db(hashes_db: dict[str, list[str]]):
    with open(HASHES_DB_FILENAME, "w") as f:
        json.dump(hashes_db, f)
    print(f"Saved hashes database with {len(hashes_db)} entries.")


def reset_hashes_db():
    hashes_db: dict[str, list[str]] = {}
    print("Hashes database reset.")
    with open(HASHES_DB_FILENAME, "w") as f:
        json.dump(hashes_db, f)


def add_file_to_db(subdir: str, filepath: str):
    hashes_db: dict[str, list[str]] = load_hashes_db()
    if subdir not in hashes_db:
        hashes_db[subdir] = []
    file_hash = subprocess.check_output(["sha256sum", filepath]).decode("utf-8").split(" ")[0]
    if not file_hash:
        raise Exception(f"Failed to compute hash for {filepath}.")
    if file_hash not in hashes_db[subdir]:
        hashes_db[subdir].append(file_hash)
        print(f"Added hash {file_hash} to subdirectory {subdir}.")
    else:
        print(f"Hash {file_hash} already exists in subdirectory {subdir}, skipping.")
    save_hashes_db(hashes_db)


def get_hashes_for_subdir(subdir: str) -> list[str]:
    hashes_db: dict[str, list[str]] = load_hashes_db()
    return hashes_db.get(subdir, [])


def get_all_hashes() -> list[str]:
    hashes_db: dict[str, list[str]] = load_hashes_db()
    lst = []
    for _, hashes in hashes_db.items():
        lst.extend(hashes)
    return lst


def exists_identical_file(filepath: str, subdir: str = "") -> bool:
    hashes_db: dict[str, list[str]] = load_hashes_db()
    file_hash = subprocess.check_output(["sha256sum", filepath]).decode("utf-8").split(" ")[0]
    if not file_hash:
        raise Exception(f"Failed to compute hash for {filepath}.")
    if subdir != "" and subdir in hashes_db and subdir != "Dateless":
        return file_hash in hashes_db.get(subdir, [])
    else:
        return file_hash in get_all_hashes()
