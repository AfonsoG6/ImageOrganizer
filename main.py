from argparse import ArgumentParser
from datetime import datetime, timedelta
import os, shutil, json, time, exiftool
from lib import hashes_db

LOG_PATH = "errors.log"

TARGET_FORMAT = "%Y-%m-%d_%H-%M-%S"

NAME_FORMATS: list[str] = [
    "%Y%m%d_%H%M%S",
    "%Y-%m-%d_%H.%M.%S",
    "%Y-%m-%d_%H-%M-%S",
    "IMG_%Y%m%d_%H%M%S",
    "Screenshot_%Y-%m-%d-%H-%M-%S",
    "Screenshot_%Y%m%d-%H%M%S",
    "MVIMG_%Y%m%d_%H%M%S",
    "VID_%Y%m%d_%H%M%S",
    "VID_%Y%m%d_%H%M%S_HDR10PLUS",
    "IMG_%Y%m%d",
    "%Y%m%d_%H%M%S",
    "VID-%Y%m%d-WA",
    "IMG-%Y%m%d-WA",
    "YIP_%Y%m%d_%H%M%S",
    "%Y-%m-%d %H-%M-%S",
    "PANO_%Y%m%d_%H%M%S",
]

HASHES_DB_FILENAME = "hashes.json"
HASHES_DB: dict[str, list[str]]

n_processed: int = 0


class Tag:
    def __init__(self, name: str):
        self.name = name

    def check(self, tags: dict):
        return self.name in tags and tags[self.name] != "0000:00:00 00:00:00" and tags[self.name] != "0000:00:00 00:00:00+00:00"

    def get(self, tags: dict):
        datestr: str = str(tags[self.name])
        if "+" in datestr:
            datestr = datestr.split("+")[0]
        # Replace invalid file name characters
        datestr = datestr.replace(":", "-").replace(" ", "_")
        return datestr

    def __str__(self):
        return self.name


class PreconditionedTag(Tag):
    def __init__(self, precondition: str, name: str):
        self.precondition = precondition
        self.name = name

    def check(self, tags: dict):
        return self.precondition in tags and super().check(tags)

    def __str__(self):
        return f"{self.precondition} -> {self.name}"


# Either a single tag or a tuple[2] with a precondition tag and the tag to check
DATE_TAGS: list[Tag] = [
    Tag("EXIF:DateTimeOriginal"),
    # Prefer embedded EXIF ModifyDate over filesystem modify date so we pick the
    # true capture/edit time (e.g. 2015) instead of a later copy time
    Tag("EXIF:ModifyDate"),
    Tag("IFD0:ModifyDate"),
    Tag("QuickTime:ModifyDate"),
    Tag("QuickTime:CreateDate"),
    # Generic/XMP/ IPTC creation dates sometimes present in edited/exported images
    Tag("XMP:DateCreated"),
    Tag("IPTC:DateCreated"),  # (paired with IPTC:TimeCreated but ExifTool may merge)
    Tag("XMP:CreateDate"),
    # ICC profile build timestamp (usually profile creation, NOT photo capture).
    # Added as a low-priority fallback only when real capture/edit dates are absent.
    Tag("ICC_Profile:ProfileDateTime"),
    PreconditionedTag("RIFF:StreamCount", "File:FileModifyDate"),
    # Disable this tag as it often reflects the copy time, not the creation time
    # Tag("File:FileModifyDate"),
]


def format_size(format: str):
    count = 0
    special = False
    for char in format:
        if special:
            if char in ["Y"]:
                count += 4
            elif char in ["m", "d", "H", "M", "S"]:
                count += 2
            else:
                count += 2
            special = False
        elif char == "%":
            special = True
        else:
            count += 1
    return count


def get_date_from_filename(filepath: str):
    filename = os.path.splitext(os.path.basename(filepath))[0]
    attempt: int = 0
    date: datetime | None = None
    while True:
        try:
            if attempt < len(NAME_FORMATS):
                aux = filename[: format_size(NAME_FORMATS[attempt])]
                date = datetime.strptime(aux, NAME_FORMATS[attempt])
                break
            else:
                break
        except:
            attempt += 1
    if date is None:
        return None
    else:
        return date.strftime(TARGET_FORMAT)


def get_file_extension(filepath: str):
    return os.path.splitext(filepath)[1].lower()


def add_delta(datestr: str, delta: int) -> str:
    if delta != 0:
        date = datetime.strptime(datestr, TARGET_FORMAT)
        # Add delta seconds to date
        date = date + timedelta(seconds=delta)
        datestr = date.strftime(TARGET_FORMAT)
    return datestr


def convert_24(datestr: str) -> str:
    if datestr.split("_")[1].startswith("24"):
        return datestr.split("_")[0] + "_00" + datestr.split("_")[1][2:]
    return datestr


def get_target_path(original_filepath: str, destination_path: str, datestr: str) -> str:
    year = datestr.split("-")[0]
    year_path = os.path.join(destination_path, year)
    if not os.path.exists(year_path):
        os.makedirs(year_path)
    target_name = datestr + get_file_extension(original_filepath)
    target_path = os.path.join(year_path, target_name)
    # If file at same second already exists, add a number to the end
    i = 0
    while os.path.exists(target_path):
        print("File", target_path, "already exists")
        i += 1
        target_name = datestr + f"_{i}" + get_file_extension(original_filepath)
        target_path = os.path.join(year_path, target_name)
    return target_path


def update_metadata(filepath: str, datestr: str):
    date_for_tags = datestr.replace("_", " ").replace("-", ":") + "+00:00"
    try:
        with exiftool.ExifToolHelper() as exif:
            exif.set_tags(
                [filepath],
                {
                    "File:FileModifyDate": date_for_tags,
                    "File:FileCreateDate": date_for_tags,
                    "EXIF:DateTimeOriginal": date_for_tags[:-6],
                },
            )
    except:
        print(f"Failed to run Exiftool on {filepath}, with date {date_for_tags}")
        with open(LOG_PATH, "a") as f:
            f.write(f"Failed to run Exiftool on {filepath}, with date {date_for_tags}\n")


def process_file(source_filepath: str, destination_path: str, delta: int = 0):
    global n_processed
    if (
        source_filepath.endswith(".py")
        or source_filepath.endswith(".json")
        or source_filepath.endswith(".txt")
        or source_filepath.endswith(".md")
        or source_filepath.endswith(".html")
        or source_filepath.endswith("_original")
    ):
        return
    with exiftool.ExifToolHelper() as exif:
        tags = exif.get_metadata([source_filepath])[0]
    for tag in DATE_TAGS:
        if tag.check(tags):
            print(f"Found date in tag {tag} for {source_filepath}")
            datestr = tag.get(tags)
            new_filepath = get_target_path(source_filepath, destination_path, datestr)
            break
    else:
        datestr = get_date_from_filename(source_filepath)
        if datestr is not None:
            print("Found date in filename for", source_filepath)
            datestr = add_delta(datestr, delta)
            datestr = convert_24(datestr)
            update_metadata(source_filepath, datestr)
            new_filepath = get_target_path(source_filepath, destination_path, datestr)
        else:
            print("No date found for", source_filepath)
            with open(LOG_PATH, "a") as f:
                f.write(f"No date found for {source_filepath} with metadata {json.dumps(tags)}\n")
            datelesspath = os.path.join(destination_path, "Dateless")
            if not os.path.exists(datelesspath):
                os.makedirs(datelesspath)
            new_filepath = os.path.join(datelesspath, os.path.basename(source_filepath))
    n_processed += 1
    subdir = os.path.basename(os.path.dirname(new_filepath))
    if hashes_db.exists_identical_file(source_filepath, subdir):
        print(f"[{n_processed}] Skipping {source_filepath} as an identical file already exists.")
    else:
        hashes_db.add_file_to_db(subdir, source_filepath)
        shutil.move(source_filepath, new_filepath)
        print(f"[{n_processed}] Moving {source_filepath} to {new_filepath}")


def process_directory(source_path: str, destination_path: str, delta: int = 0):
    print("Fixing directory", source_path)
    for name in os.listdir(source_path):
        path: str = os.path.join(source_path, name)
        if os.path.isdir(path) and not name.startswith(".") and not name == destination_path:
            process_directory(os.path.join(source_path, name), destination_path, delta)
        elif os.path.isfile(path):
            process_file(os.path.join(source_path, name), destination_path, delta)
        else:
            print("Ignoring", name)


if __name__ == "__main__":
    parser = ArgumentParser(description="Fix photos in a directory")
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        required=True,
        help="Directory from which to read files",
    )
    parser.add_argument(
        "--destination",
        "-d",
        type=str,
        required=True,
        help="Directory to move files to",
    )
    parser.add_argument(
        "--delta",
        "-D",
        type=int,
        default=0,
        required=False,
        help="Timezone difference in seconds",
    )
    args = parser.parse_args()

    source_path = args.source
    destination_path = args.destination
    delta = args.delta

    os.makedirs(destination_path, exist_ok=True)
    hashes_db.load_hashes_db(destination_path)
    process_directory(source_path, destination_path, delta)
    hashes_db.save_hashes_db()
