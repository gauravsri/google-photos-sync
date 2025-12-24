import os
import sys
import json
import subprocess
import argparse
import re
import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Sets up logging to both console and a file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"takeout_fixer_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

def parse_json_metadata(json_path):
    """Reads Google Takeout JSON and extracts date and GPS."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Extract Timestamp
        timestamp = data.get('photoTakenTime', {}).get('timestamp')
        date_str = None
        if timestamp:
            dt = datetime.fromtimestamp(int(timestamp))
            date_str = dt.strftime("%Y:%m:%d %H:%M:%S")

        # Extract GPS
        geo = data.get('geoData', {})
        lat = geo.get('latitude')
        lon = geo.get('longitude')
        alt = geo.get('altitude')
        
        return date_str, lat, lon, alt
    except Exception as e:
        logging.error(f"Error parsing {json_path}: {e}")
        return None, None, None, None

def find_json_for_file(file_path):
    """Tries to find the matching JSON file with messy Takeout naming."""
    name = file_path.name
    # 1. Exact append: IMG_1234.JPG.json
    p1 = file_path.with_name(name + ".json")
    if p1.exists(): return p1

    # 2. Duplicate handling: IMG_1234(1).JPG -> IMG_1234.JPG(1).json
    match = re.search(r'(.*)(\(\d+\))(\.\w+)$', name)
    if match:
        base, num, ext = match.groups()
        p2 = file_path.with_name(f"{base}{ext}{num}.json")
        if p2.exists(): return p2

    # 3. Truncation handling (approx 47-51 chars)
    p3 = file_path.with_name(name[:47] + ".json")
    if p3.exists(): return p3

    # 4. Extension replacement: IMG_1234.json
    p4 = file_path.with_suffix(".json")
    if p4.exists(): return p4
    
    return None

def fix_metadata(image_path, json_path, output_dir=None, dry_run=False):
    """Applies metadata from JSON to Image using exiftool and optionally moves it."""
    date_str, lat, lon, alt = parse_json_metadata(json_path)
    
    if not date_str:
        logging.warning(f"Skipping {image_path.name}: No valid date in JSON.")
        return

    # 1. Update Metadata
    cmd = ['exiftool', '-overwrite_original']
    cmd.append(f'-DateTimeOriginal={date_str}')
    cmd.append(f'-CreateDate={date_str}')
    cmd.append(f'-ModifyDate={date_str}')
    
    if lat and lon and (lat != 0.0 or lon != 0.0):
        cmd.append(f'-GPSLatitude={lat}')
        cmd.append(f'-GPSLongitude={lon}')
        cmd.append(f'-GPSLatitudeRef={lat}')
        cmd.append(f'-GPSLongitudeRef={lon}')
        if alt:
             cmd.append(f'-GPSAltitude={alt}')

    cmd.append(str(image_path))

    if dry_run:
        logging.info(f"[DRY RUN] Would fix: {image_path.name}")
    else:
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error fixing {image_path.name}: {e.stderr.decode().strip()}")
            return

    # 2. Optional: Move to Output Directory
    if output_dir:
        dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        year_month_dir = Path(output_dir).expanduser() / str(dt.year) / f"{dt.month:02d}"
        if not dry_run:
            year_month_dir.mkdir(parents=True, exist_ok=True)
            new_path = year_month_dir / image_path.name
            
            counter = 1
            while new_path.exists():
                new_path = year_month_dir / f"{image_path.stem}_{counter}{image_path.suffix}"
                counter += 1
            
            image_path.rename(new_path)
            logging.info(f"Fixed and Moved: {image_path.name} -> {new_path.relative_to(Path(output_dir).expanduser())}")
        else:
            logging.info(f"[DRY RUN] Would move {image_path.name} to {year_month_dir}")
    else:
        logging.info(f"Fixed: {image_path.name}")

def main():
    log_file = setup_logging()
    
    default_output = "~/Downloads/GooglePhotosFixed"
    
    parser = argparse.ArgumentParser(description="Fix Google Takeout Photo Metadata")
    parser.add_argument("input_dir", help="Directory containing photos and JSONs")
    parser.add_argument("--output-dir", default=default_output, help=f"Directory to move fixed files to (default: {default_output})")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually modify files")
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    if not input_path.exists():
        logging.error(f"Input directory {args.input_dir} does not exist.")
        return

    output_path = Path(args.output_dir).expanduser()
    if not output_path.exists() and not args.dry_run:
        output_path.mkdir(parents=True)

    logging.info(f"Starting run. Logs: {log_file}")
    logging.info(f"Input: {input_path}")
    logging.info(f"Output: {output_path}")

    extensions = {'.jpg', '.jpeg', '.png', '.heic', '.mov', '.mp4', '.m4v'}
    
    count = 0
    for root, _, files in os.walk(input_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in extensions:
                json_path = find_json_for_file(file_path)
                if json_path:
                    fix_metadata(file_path, json_path, str(output_path), args.dry_run)
                    count += 1
    
    logging.info(f"Finished. Processed {count} files.")

if __name__ == "__main__":
    main()
