# Google Photos Takeout Fixer

A Python-based CLI tool to fix metadata (Date Taken, GPS) and organize photos/videos from Google Takeout.

## The Problem
Google Takeout exports your media in a "messy" way:
1.  **Metadata Separation:** Important data like "Date Taken" and GPS coordinates are often stripped from the image/video files and placed in separate `.json` "sidecar" files.
2.  **Date Reset:** File system creation dates are often reset to the date you downloaded the archive.
3.  **Naming Mess:** Google handles duplicate filenames or long filenames by appending suffixes like `(1)` or truncating them, making it hard to match JSON files to images.

## The Solution
This script automates the process of:
1.  **Matching:** Intelligently matching images/videos with their correct JSON metadata files.
2.  **Injecting:** Using `exiftool` to write the correct "Date Taken" and GPS data back into the files' EXIF/XMP headers.
3.  **Organizing:** Moving the fixed files into a clean `Year/Month` folder structure.

## Requirements
- **Python 3.10+**
- **exiftool**: The script relies on the industry-standard `exiftool` for metadata writing.
  - MacOS: `brew install exiftool`
  - Linux: `sudo apt-get install exiftool`

## Installation

1. Clone the repository.
2. Set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

## Usage

1. **Download your Takeout:** Go to [takeout.google.com](https://takeout.google.com) and export your Google Photos library. Unzip the archive.
2. **Run the Fixer:**

   ```bash
   # Default: Organizes files into ~/Downloads/GooglePhotosFixed
   python3 takeout_fixer.py /path/to/your/unzipped/takeout

   # Custom Output Directory:
   python3 takeout_fixer.py /path/to/your/unzipped/takeout --output-dir ./MyPhotos
   ```

### Options
- `--output-dir`: Where to move the fixed files (organized by Year/Month). Defaults to `~/Downloads/GooglePhotosFixed`.
- `--dry-run`: See what would happen without modifying or moving any files.
- `--help`: Show available commands.

## Logging
Logs for every run are saved in the `./logs/` directory, detailing exactly which files were processed, fixed, and moved.

## Supported Formats
- **Images:** `.jpg`, `.jpeg`, `.png`, `.heic`
- **Videos:** `.mov`, `.mp4`, `.m4v`