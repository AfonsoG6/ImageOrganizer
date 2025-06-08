import json, os, subprocess

HASHES_DB_FILENAME = "hashes.json"
_hashes_db_cache: dict[str, list[str]] = {}  # In-memory cache for the hashes database
_library_path_cache: str = ""  # Cache for the library path to avoid repeated disk access

def load_hashes_db(library_path: str):
    """Load the hashes database into memory."""
    global _hashes_db_cache, _library_path_cache
    if _library_path_cache == library_path:
        return  # Avoid reloading if the library path is the same
    _library_path_cache = library_path
    if not os.path.exists(os.path.join(library_path, HASHES_DB_FILENAME)):
        _hashes_db_cache = {}
        return
    with open(os.path.join(library_path, HASHES_DB_FILENAME), "r") as f:
        _hashes_db_cache = json.load(f)


def save_hashes_db():
    """Save the in-memory hashes database to disk."""
    global _hashes_db_cache, _library_path_cache
    with open(os.path.join(_library_path_cache, HASHES_DB_FILENAME), "w") as f:
        json.dump(_hashes_db_cache, f)


def reset_hashes_db(library_path: str):
    """Reset the in-memory hashes database and save it to disk."""
    global _hashes_db_cache, _library_path_cache
    _hashes_db_cache = {}
    _library_path_cache = library_path
    save_hashes_db()
    print("Hashes database reset.")


def add_file_to_db(subdir: str, filepath: str):
    """Add a file's hash to the in-memory database."""
    global _hashes_db_cache
    if subdir not in _hashes_db_cache:
        _hashes_db_cache[subdir] = []
    attempt = 0
    while True:
        try:
            file_hash = subprocess.check_output(["sha256sum", filepath]).decode("utf-8").split(" ")[0]
            break
        except:
            attempt += 1
            if attempt >= 3:
                raise Exception(f"Failed to compute hash for {filepath} after 3 attempts.")
    if not file_hash:
        raise Exception(f"Failed to compute hash for {filepath}.")
    if file_hash not in _hashes_db_cache[subdir]:
        _hashes_db_cache[subdir].append(file_hash)
        print(f"Added hash {file_hash} to subdirectory {subdir}.")
    else:
        print(f"Hash {file_hash} already exists in subdirectory {subdir}, skipping.")
    save_hashes_db()  # Save changes to disk


def get_hashes_for_subdir(subdir: str) -> list[str]:
    """Retrieve hashes for a specific subdirectory from the in-memory database."""
    global _hashes_db_cache
    return _hashes_db_cache.get(subdir, [])


def get_all_hashes() -> list[str]:
    """Retrieve all hashes from the in-memory database."""
    global _hashes_db_cache
    lst = []
    for _, hashes in _hashes_db_cache.items():
        lst.extend(hashes)
    return lst


def exists_identical_file(filepath: str, subdir: str = "") -> bool:
    """Check if a file with the same hash exists in the in-memory database."""
    global _hashes_db_cache
    attempt = 0
    while True:
        try:
            file_hash = subprocess.check_output(["sha256sum", filepath]).decode("utf-8").split(" ")[0]
            break
        except:
            attempt += 1
            if attempt >= 3:
                raise Exception(f"Failed to compute hash for {filepath} after 3 attempts.")
    if not file_hash:
        raise Exception(f"Failed to compute hash for {filepath}.")
    if subdir != "" and subdir in _hashes_db_cache and subdir != "Dateless":
        return file_hash in _hashes_db_cache.get(subdir, [])
    else:
        return file_hash in get_all_hashes()
