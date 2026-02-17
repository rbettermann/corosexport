# Corosexport - Coros Activity Exporter

A Python library and command-line tool for downloading and backing up Coros activities to your local machine, similar to the popular [garminexport](https://github.com/petergardfjall/garminexport) for Garmin devices.

## Features

- **Incremental Backups** - First run downloads all activities, subsequent runs only grab new ones
- **Multiple Formats** - Export activities as FIT, TCX, GPX, KML or CSV
- **Library & CLI** - Use as a standalone tool or import into your own Python projects
- **Cross-Platform** - Works on macOS, Linux, and Windows
- **State Tracking** - Automatically tracks which activities have been backed up

## Quick Start

### Installation

#### With uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/rbettermann/corosexport.git
cd corosexport

# Install with uv
uv sync

# Run the CLI
uv run coros-backup
```

#### With pip

```bash
pip install corosexport
coros-backup --backup-dir=./coros_activities
```

### First Backup

```bash
coros-backup --backup-dir=~/coros_activities
```

The tool will prompt for your Coros email and password, then:
1. Authenticate with Coros Training Hub
2. Fetch all activities
3. Download files in your specified formats
4. Save a state file for future incremental backups

### Incremental Backups

Run the same command again - it will only download new activities:

```bash
coros-backup --backup-dir=~/coros_activities --format fit --format tcx
```

## Development Setup

### Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (for fast package management)

### Setup Development Environment

```bash
git clone https://github.com/yourusername/corosexport.git
cd corosexport

# Install all dependencies including dev tools
uv sync

# Run tests
uv run pytest -v

# Run with verbose logging
uv run coros-backup --verbose

# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## API Usage (as Library)

Use `corosexport` in your own Python projects:

```python
from pathlib import Path
from corosexport import CorosClient, BackupManager
from corosexport.models import ExportFormat

# Create and authenticate client
client = CorosClient(email="user@example.com", password="your_password")
client.authenticate()

# Fetch activities
activities = client.get_activities(limit=50)
for activity in activities:
    print(f"{activity.activity_name}: {activity.distance_meters}m")

# Setup backup manager
backup_manager = BackupManager(
    client=client,
    backup_dir=Path("./coros_activities"),
    formats=[ExportFormat.FIT, ExportFormat.TCX],
)

# Run backup
stats = backup_manager.run_backup()
print(f"Downloaded {stats['activities_downloaded']} new activities")
```

## Backup Directory Structure

After running backups, your directory looks like this:

```
coros_activities/
├── .corosexport_state.json                  # Internal state file (do not edit)
├── 2025-01-10_activity-001-metadata.json    # Activity summary data
├── 2025-01-10_activity-001.fit              # Raw FIT file
├── 2025-01-10_activity-001.tcx              # TCX format
├── 2025-01-10_activity-001.gpx              # GPX format
├── 2025-01-11_activity-002-metadata.json
├── 2025-01-11_activity-002.fit
├── 2025-01-11_activity-002.tcx
├── 2025-01-11_activity-002.gpx
├── ...
```

**metadata.json** contains:
- Activity ID, name, type
- Distance (meters)
- Start time, end time, workout duration, total duration


## Command-Line Options

```bash
coros-backup --help

Options:
  --backup-dir TEXT     Directory to store activities (default: ./coros_activities)
  --email TEXT          Coros account email
  --password TEXT       Coros password (prompts if omitted for security)
  --format TEXT         Export formats: fit, tcx, gpx, kml or csv
  --verbose             Enable debug logging
  --help                Show this message
```

### Examples

```bash
# Backup to specific directory
coros-backup --backup-dir ~/fitness_backups

# Download only FIT files
coros-backup --format fit

# Download all formats
coros-backup --format fit --format tcx --format gpx

# Enable verbose output
coros-backup --backup-dir ~/coros --verbose
```

## Architecture Notes

### Reverse-Engineered APIs

This project uses reverse-engineered APIs from the Coros Training Hub web interface. The endpoints used are:


- `POST /account/login` - Authentication
- `GET /activity/query` - List activities
- `GET /activity/detail/download` - Download activity files


These are not officially documented by Coros. This tool is for personal data backup only.

### State Management

Backups are incremental using a `.corosexport_state.json` file that tracks:
- When the last backup completed
- Which activity IDs have been downloaded
- Total activities backed up

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/corosexport

# Run specific test file
uv run pytest tests/test_client.py -v

# Run with verbose output
uv run pytest -v -s
```


## Disclaimer

This tool is for personal data backup only. While Coros has not explicitly prohibited API access via their Terms of Service, they have not published official APIs either. Use at your own discretion and respect Coros' services.

## License

Apache License 2.0 - See LICENSE file for details

## Related Projects

- [garminexport](https://github.com/petergardfjall/garminexport) - Similar tool for Garmin devices
- [strava-offline](https://github.com/liskin/strava-offline) - Strava activity backup

## FAQ

**Q: Is this tool affiliated with Coros?**
A: No, this is a community project created for personal data archival.

**Q: Does this work with the Coros mobile app?**
A: No, this tool works with the Coros Training Hub web interface.

**Q: Can I upload activities back to Coros?**
A: Not currently, but this could be added in future versions.

**Q: What about my password security?**
A: Passwords are only used to authenticate and are never stored. They're passed directly to Coros' servers over HTTPS.
