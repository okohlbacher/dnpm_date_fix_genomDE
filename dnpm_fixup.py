#!/usr/bin/env python3
"""
DNPM submission data fix-up tool

A CLI tool for fixing submission dates in DNPM patient record and submission report files.

MIT License

Copyright (c) 2025 Oliver Kohlbacher

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    epilog = """
Config File Format:
  CSV file with no header. Each line contains:
    <TAN>,<ISO_8601_DATETIME>

  Example:
    306600442D212C47921B7DC0C8C2A886...,2025-10-15T14:30:00.000000000

  The TAN is a 64-character hexadecimal transfer identifier.
  The datetime format is: YYYY-MM-DDTHH:MM:SS.nnnnnnnnn (nanosecond precision)

Input File Types:
  1. Patient Records (MVH_MTBPatientRecord_Patient_<UUID>_TAN_<TAN>.json)
     - JSON file containing patient medical records with nested structure
     - TAN read from: metadata.transferTAN (top-level metadata object)
     - Field replaced: submittedAt (top-level, ISO 8601 datetime string)
     - Contains: patient demographics, episodes of care, diagnoses, treatments

  2. Submission Reports (SubmissionReport_Patient_<UUID>_TAN_<TAN>.json)
     - JSON file containing submission metadata
     - TAN read from: id (top-level field)
     - Field replaced: createdAt (top-level, ISO 8601 datetime string)
     - Contains: id, createdAt, patient UUID, status, site, useCase, type

Only files with TANs matching config entries are written to the output directory.
Files are written with UTF-8 encoding and 2-space indentation.

License:
  MIT License
"""
    parser = argparse.ArgumentParser(
        prog='dnpm_fixup.py',
        description='DNPM submission data fix-up tool - Corrects submission dates in patient record and submission report files.',
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--config',
        required=True,
        metavar='<config_filename>',
        help='CSV config file with TAN,DATE pairs (no header). Date format: YYYY-MM-DDTHH:MM:SS.nnnnnnnnn'
    )
    parser.add_argument(
        '--in-dir',
        required=True,
        metavar='<input_directory>',
        help='Input directory containing MVH_MTBPatientRecord_*.json and SubmissionReport_*.json files'
    )
    parser.add_argument(
        '--out-dir',
        required=True,
        metavar='<output_directory>',
        help='Output directory for corrected JSON files (must already exist)'
    )

    return parser.parse_args()


def validate_paths(config_path: str, in_dir: str, out_dir: str) -> bool:
    """Validate that config file and directories exist."""
    if not os.path.isfile(config_path):
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        return False

    if not os.path.isdir(in_dir):
        print(f"Error: Input directory not found: {in_dir}", file=sys.stderr)
        return False

    if not os.path.isdir(out_dir):
        print(f"Error: Output directory not found: {out_dir}", file=sys.stderr)
        return False

    return True


def parse_config_file(config_path: str) -> Dict[str, str]:
    """
    Parse the CSV config file and return a dictionary mapping TAN to date.

    Args:
        config_path: Path to the CSV config file

    Returns:
        Dictionary mapping TAN values to ISO date strings
    """
    tan_date_map = {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    tan = row[0].strip()
                    date = row[1].strip()
                    if tan and date:
                        tan_date_map[tan] = date
    except Exception as e:
        print(f"Error reading config file: {e}", file=sys.stderr)
        return {}

    return tan_date_map


def get_json_files(in_dir: str) -> Tuple[List[str], List[str]]:
    """
    Get lists of patient record files and submission report files from input directory.

    Args:
        in_dir: Path to input directory

    Returns:
        Tuple of (patient_record_files, submission_report_files)
    """
    patient_record_files = []
    submission_report_files = []

    for filename in os.listdir(in_dir):
        if not filename.endswith('.json'):
            continue

        filepath = os.path.join(in_dir, filename)
        if not os.path.isfile(filepath):
            continue

        if filename.startswith('MVH_MTBPatientRecord_Patient'):
            patient_record_files.append(filename)
        elif filename.startswith('SubmissionReport_Patient'):
            submission_report_files.append(filename)

    return patient_record_files, submission_report_files


def process_patient_record(filepath: str, tan_date_map: Dict[str, str]) -> Optional[Tuple[str, str, dict]]:
    """
    Process a patient record file and check if it needs fixing.

    Args:
        filepath: Path to the patient record JSON file
        tan_date_map: Dictionary mapping TAN to new date

    Returns:
        Tuple of (TAN, new_date, modified_data) if file needs fixing, None otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: File is not valid JSON: {filepath} - {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error reading file: {filepath} - {e}", file=sys.stderr)
        return None

    # Extract TAN from metadata.transferTAN
    try:
        tan = data.get('metadata', {}).get('transferTAN')
    except (AttributeError, TypeError):
        tan = None

    if not tan:
        print(f"Warning: Could not extract transferTAN from: {filepath}", file=sys.stderr)
        return None

    # Check if TAN is in our fix list
    if tan not in tan_date_map:
        return None

    # Update submittedAt field
    new_date = tan_date_map[tan]
    data['submittedAt'] = new_date

    return (tan, new_date, data)


def process_submission_report(filepath: str, tan_date_map: Dict[str, str]) -> Optional[Tuple[str, str, dict]]:
    """
    Process a submission report file and check if it needs fixing.

    Args:
        filepath: Path to the submission report JSON file
        tan_date_map: Dictionary mapping TAN to new date

    Returns:
        Tuple of (TAN, new_date, modified_data) if file needs fixing, None otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: File is not valid JSON: {filepath} - {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error reading file: {filepath} - {e}", file=sys.stderr)
        return None

    # Extract TAN from id field
    tan = data.get('id')

    if not tan:
        print(f"Warning: Could not extract id from: {filepath}", file=sys.stderr)
        return None

    # Check if TAN is in our fix list
    if tan not in tan_date_map:
        return None

    # Update createdAt field
    new_date = tan_date_map[tan]
    data['createdAt'] = new_date

    return (tan, new_date, data)


def write_output_file(out_dir: str, filename: str, data: dict) -> bool:
    """
    Write modified JSON data to output file.

    Args:
        out_dir: Output directory path
        filename: Name of the file to create
        data: JSON data to write

    Returns:
        True if successful, False otherwise
    """
    filepath = os.path.join(out_dir, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error writing file: {filepath} - {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the DNPM fix-up tool."""
    args = parse_arguments()

    # Validate paths
    if not validate_paths(args.config, args.in_dir, args.out_dir):
        sys.exit(1)

    # Parse config file
    tan_date_map = parse_config_file(args.config)
    if not tan_date_map:
        print("Error: No valid TAN/date pairs found in config file", file=sys.stderr)
        sys.exit(1)

    print(f"Number of TAN/date pairs to fix: {len(tan_date_map)}")

    # Get JSON files from input directory
    patient_record_files, submission_report_files = get_json_files(args.in_dir)

    print(f"Found {len(patient_record_files)} patient record files")
    print(f"Found {len(submission_report_files)} submission report files")

    modified_count = 0
    error_count = 0

    # Process patient record files
    for filename in patient_record_files:
        filepath = os.path.join(args.in_dir, filename)
        result = process_patient_record(filepath, tan_date_map)

        if result:
            tan, new_date, data = result
            if write_output_file(args.out_dir, filename, data):
                print(f"Fixed patient record - TAN: {tan}, Date: {new_date}")
                modified_count += 1
            else:
                error_count += 1

    # Process submission report files
    for filename in submission_report_files:
        filepath = os.path.join(args.in_dir, filename)
        result = process_submission_report(filepath, tan_date_map)

        if result:
            tan, new_date, data = result
            if write_output_file(args.out_dir, filename, data):
                print(f"Fixed submission report - TAN: {tan}, Date: {new_date}")
                modified_count += 1
            else:
                error_count += 1

    # Summary
    print(f"\nSummary:")
    print(f"  Files modified: {modified_count}")
    if error_count > 0:
        print(f"  Errors encountered: {error_count}")


if __name__ == '__main__':
    main()
