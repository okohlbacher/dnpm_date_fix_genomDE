# DNPM submission data fix-up tool

## Overview

A Python CLI tool for correcting submission dates in DNPM patient record and submission report JSON files.

## Requirements

- Python 3.9+
- Cross-platform (Windows, macOS, Linux)
- Executes from the command line
- Command line parameters specify an input directory, output directory, and config file
- Input files reside in the specified input directory
- Output files are created only in the specified output directory
- Input and output files are valid JSON files with UTF-8 encoding

## File Types

### Patient Record Files
- Filename pattern: `MVH_MTBPatientRecord_Patient_<UUID>_TAN_<TAN>.json`
- JSON file containing patient medical records with nested structure
- TAN read from: `metadata.transferTAN` (top-level metadata object)
- Field replaced: `submittedAt` (top-level, ISO 8601 datetime string)
- Contains: patient demographics, episodes of care, diagnoses, treatments

### Submission Report Files
- Filename pattern: `SubmissionReport_Patient_<UUID>_TAN_<TAN>.json`
- JSON file containing submission metadata
- TAN read from: `id` (top-level field)
- Field replaced: `createdAt` (top-level, ISO 8601 datetime string)
- Contains: id, createdAt, patient UUID, status, site, useCase, type

### Config File Format
- CSV file with no header
- Each line contains: `<TAN>,<ISO_8601_DATETIME>`
- TAN: 64-character hexadecimal transfer identifier
- Datetime format: `YYYY-MM-DDTHH:MM:SS.nnnnnnnnn` (nanosecond precision)
- Example: `306600442D212C47921B7DC0C8C2A886...,2025-10-15T14:30:00.000000000`

## Command Structure

0. When called without parameters or with the `--help` parameter, the tool displays its usage
1. The tool's name is `dnpm_fixup.py`
2. Required parameters:
   - `--config <config_filename>` - CSV config file with TAN,DATE pairs
   - `--in-dir <input_directory>` - Input directory containing JSON files
   - `--out-dir <output_directory>` - Output directory for corrected files

## Functionality

1. Check whether the input and output directories exist. Abort if they cannot be found or if the config file cannot be found
2. Parse the config file and print the number of TAN/date pairs to fix
3. Scan input directory for patient record files and submission report files
4. For each file:
   - Parse the JSON content
   - Extract TAN (from `metadata.transferTAN` for patient records, `id` for submission reports)
   - If TAN matches an entry in the config file:
     - Create a copy in the output directory with the same filename
     - Replace `submittedAt` (patient record) or `createdAt` (submission report) with the new date
     - Write the modified JSON with UTF-8 encoding and 2-space indentation
     - Print the TAN and new date to console

## Error Handling

- Report how many files have been modified
- Report any errors to the console
- If directories or config file cannot be found, print error and abort
- If a file cannot be read or is not valid JSON, print error and continue with next file

## Examples

Test data files are provided in the `Test Data` directory.
A sample config file is provided as `sample_config.csv`.

## Repository

https://github.com/okohlbacher/dnpm_date_fix_genomDE

## License

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
