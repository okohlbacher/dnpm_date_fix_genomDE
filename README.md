# DNPM Submission Date Fix-up Tool

A Python CLI utility for correcting submission dates in DNPM (German Network for Personalized Medicine) patient record and submission report files.

## Overview

This tool reads a configuration file containing TAN (Transaction Authentication Number) and corrected date pairs, scans an input directory for matching JSON files, updates the relevant date fields, and writes the corrected files to an output directory.

## Requirements

- Python 3.9 or higher
- No external dependencies (uses only standard library)
- Cross-platform: Windows, macOS, Linux

## Installation

No installation required. Simply download or clone the repository and run the script directly:

```bash
python dnpm_fixup.py --help
```

## Usage

```bash
python dnpm_fixup.py --config <config_file> --in-dir <input_directory> --out-dir <output_directory>
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--config` | Yes | Path to the CSV configuration file containing TAN and date pairs |
| `--in-dir` | Yes | Path to the input directory containing JSON files to process |
| `--out-dir` | Yes | Path to the output directory where corrected files will be written |
| `--help` | No | Display help message and exit |

### Example

```bash
python dnpm_fixup.py --config sample_config.csv --in-dir "Test Data" --out-dir output
```

## Configuration File Format

The configuration file is a CSV file (comma-separated values) with **no header row**. Each line contains two values:

1. **TAN** - A 64-character hexadecimal Transaction Authentication Number
2. **Date** - An ISO 8601 datetime string with nanosecond precision

### Format

```
<TAN>,<ISO_8601_DATETIME>
```

### Example Config File

```csv
306600442D212C47921B7DC0C8C2A886AEE7802ECF00F715F474C5BDE4CF3F5C,2025-10-15T14:30:00.000000000
5ABBAD9AF73B5DBED332841901586D50EC0CEEA6D8115C40DB1E2C2B197B8E52,2025-10-16T09:15:30.000000000
```

### Date Format Details

The date must be in ISO 8601 format: `YYYY-MM-DDTHH:MM:SS.nnnnnnnnn`

- `YYYY-MM-DD` - Date (year, month, day)
- `T` - Separator
- `HH:MM:SS` - Time (hours, minutes, seconds)
- `.nnnnnnnnn` - Nanoseconds (9 digits)

## Input File Types

The tool processes two types of JSON files from the input directory:

### 1. Patient Record Files

- **Filename pattern**: `MVH_MTBPatientRecord_Patient*.json`
- **TAN location**: `metadata.transferTAN`
- **Field replaced**: `submittedAt`

Example structure:
```json
{
  "submittedAt": "2025-01-10T12:00:00.000000000",
  "metadata": {
    "transferTAN": "306600442D212C47921B7DC0C8C2A886AEE7802ECF00F715F474C5BDE4CF3F5C"
  },
  ...
}
```

### 2. Submission Report Files

- **Filename pattern**: `SubmissionReport_Patient*.json`
- **TAN location**: `id`
- **Field replaced**: `createdAt`

Example structure:
```json
{
  "id": "306600442D212C47921B7DC0C8C2A886AEE7802ECF00F715F474C5BDE4CF3F5C",
  "createdAt": "2025-01-10T12:00:00.000000000",
  ...
}
```

## Fields Modified

| File Type | TAN Source Field | Date Field Modified |
|-----------|------------------|---------------------|
| Patient Record (`MVH_MTBPatientRecord_*`) | `metadata.transferTAN` | `submittedAt` |
| Submission Report (`SubmissionReport_*`) | `id` | `createdAt` |

## Output

- Only files with TANs matching entries in the config file are written to the output directory
- Output files retain their original filenames
- JSON is formatted with 2-space indentation
- Files without matching TANs are skipped (not copied)

### Console Output

The tool prints progress information to stdout:
```
Number of TAN/date pairs to fix: 2
Found 6 patient record files
Found 6 submission report files
Fixed patient record - TAN: 306600442D212C47921B7DC0C8C2A886..., Date: 2025-10-15T14:30:00.000000000
Fixed submission report - TAN: 306600442D212C47921B7DC0C8C2A886..., Date: 2025-10-15T14:30:00.000000000

Summary:
  Files modified: 4
```

## Error Handling

- **Missing paths**: The tool aborts if the config file or directories don't exist
- **Invalid JSON**: Files that aren't valid JSON are skipped with an error message
- **Missing TAN**: Files without the expected TAN field are skipped with a warning
- **Write errors**: Failed writes are reported but don't stop processing

Errors are printed to stderr, allowing you to separate them from normal output:
```bash
python dnpm_fixup.py --config config.csv --in-dir input --out-dir output 2>errors.log
```

## Project Structure

```
SubmissionDateFix-DNPM/
├── dnpm_fixup.py        # Main tool script
├── README.md            # This documentation
├── Spec.md              # Technical specification
├── sample_config.csv    # Example configuration file
├── Test Data/           # Sample input files for testing
│   ├── MVH_MTBPatientRecord_Patient*.json
│   └── SubmissionReport_Patient*.json
└── output/              # Default output directory
```

## License

Internal tool for UKE DNPM data processing.
