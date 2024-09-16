# Python Image Organizer

This Python script is designed to organize and fix metadata dates of photos and videos within a directory. It retrieves dates from either metadata tags or from filenames, renames the files accordingly, and updates the metadata. The script supports various filename formats and organizes files into directories by year.

## Features

- Extracts date information from EXIF metadata or filename.
- Renames files based on date in the format `YYYY-MM-DD_HH-MM-SS`.
- Organizes files into directories by year.
- Updates the metadata of the files with the correct date and time.
- Supports custom timezone deltas for date adjustments.
- Handles a variety of filename formats (e.g., `IMG_20210923_101112`, `Screenshot_2021-09-23-10-11-12`).
- Logs errors and warnings for files without date information or problematic metadata.

## Requirements

- Python 3.8 or higher
- [ExifTool](https://exiftool.org/) (used for reading and updating metadata)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/AfonsoG6/ImageOrganizer.git
    ```

2. Navigate to the project directory:

    ```bash
    cd ImageOrganizer
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from the command line with the following options:

```bash
python3 photo_date_fixer.py --directory <directory_to_fix> --output <output_directory> [--delta <delta_in_seconds>]
```

### Arguments

- `--directory` or `-d`: The directory containing the photos or videos to fix.
- `--output` or `-o`: The directory where the fixed files will be saved (default: `output`).
- `--delta` or `-D`: Time to add in seconds for correcting time zones (default: `0`).

### Example

To process files in the `photos` directory and save the fixed files in `output` with a timezone delta of 2 hours (7200 seconds):

```bash
python3 main.py --directory photos --output output --delta 7200
```

## Supported Filename Date Formats

The script recognizes the following filename patterns:

- `%Y%m%d_%H%M%S`
- `%Y-%m-%d_%H.%M.%S`
- `%Y-%m-%d_%H-%M-%S`
- `IMG_%Y%m%d_%H%M%S`
- `Screenshot_%Y-%m-%d-%H-%M-%S`
- `Screenshot_%Y%m%d-%H%M%S`
- `MVIMG_%Y%m%d_%H%M%S`
- `VID_%Y%m%d_%H%M%S`
- `IMG_%Y%m%d`
- `%Y%m%d_%H%M%S`
- `VID-%Y%m%d-WA`
- `IMG-%Y%m%d-WA`
- `YIP_%Y%m%d_%H%M%S`
- `%Y-%m-%d %H-%M-%S`

## License

This project is licensed under the GPL-3.0 license.
