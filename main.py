from argparse import ArgumentParser
from datetime import datetime, timedelta
import os, shutil, json, exiftool

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
    "IMG_%Y%m%d",
    "%Y%m%d_%H%M%S",
    "VID-%Y%m%d-WA",
    "IMG-%Y%m%d-WA",
    "YIP_%Y%m%d_%H%M%S",
    "%Y-%m-%d %H-%M-%S",
]


class Tag:
    def __init__(self, name: str):
        self.name = name

    def check(self, tags: dict):
        return (
            self.name in tags
            and tags[self.name] != "0000:00:00 00:00:00"
            and tags[self.name] != "0000:00:00 00:00:00+00:00"
        )

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
    Tag("QuickTime:ModifyDate"),
    Tag("QuickTime:CreateDate"),
    PreconditionedTag("RIFF:StreamCount", "File:FileModifyDate"),
    Tag("File:FileModifyDate"),
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


def get_target_path(original_filepath: str, datestr: str) -> str:
    year = datestr.split("-")[0]
    year_path = os.path.join(outpath, year)
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
            f.write(
                f"Failed to run Exiftool on {filepath}, with date {date_for_tags}\n"
            )


def process_file(filepath: str, outpath: str, delta: int = 0):
    if (
        filepath.endswith(".py")
        or filepath.endswith(".json")
        or filepath.endswith(".txt")
        or filepath.endswith(".md")
        or filepath.endswith(".html")
    ):
        return
    processed: int = 0
    with exiftool.ExifToolHelper() as exif:
        tags = exif.get_metadata([filepath])[0]
    for tag in DATE_TAGS:
        if tag.check(tags):
            print(f"Found date in tag {tag} for {filepath}")
            datestr = tag.get(tags)
            break
    else:
        datestr = get_date_from_filename(filepath)
        if datestr is not None:
            print("Found date in filename for", filepath)
            datestr = add_delta(datestr, delta)
            datestr = convert_24(datestr)
            new_filepath = get_target_path(filepath, datestr)
            processed += 1
            shutil.move(filepath, new_filepath)
            update_metadata(new_filepath, datestr)
            print(f"[{processed}] Moving/Renaming {filepath} to {new_filepath}")
        else:
            print("No date found for", filepath)
            with open(LOG_PATH, "a") as f:
                f.write(
                    f"No date found for {filepath} with metadata {json.dumps(tags)}\n"
                )
            datelesspath = os.path.join(outpath, "Dateless")
            if not os.path.exists(datelesspath):
                os.makedirs(datelesspath)
            new_filepath = os.path.join(datelesspath, os.path.basename(filepath))
            processed += 1
            shutil.move(filepath, new_filepath)
            print(f"[{processed}] Moving {filepath} to {new_filepath}")
            return


def process_directory(dirpath: str, outpath: str, delta: int = 0):
    print("Fixing directory", dirpath)
    for name in os.listdir(dirpath):
        path: str = os.path.join(dirpath, name)
        if os.path.isdir(path) and not name.startswith(".") and not name == outpath:
            process_directory(os.path.join(dirpath, name), outpath, delta)
        elif os.path.isfile(path):
            process_file(os.path.join(dirpath, name), outpath, delta)
        else:
            print("Ignoring", name)


if __name__ == "__main__":
    parser = ArgumentParser(description="Fix photos in a directory")
    parser.add_argument(
        "--directory", "-d", type=str, required=True, help="Directory to fix"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output",
        required=False,
        help="Output directory",
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

    dirpath = args.directory
    outpath = args.output
    delta = args.delta
    os.makedirs(args.output, exist_ok=True)
    process_directory(dirpath, outpath, delta)
