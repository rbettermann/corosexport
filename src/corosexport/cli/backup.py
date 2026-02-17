"""Command-line interface for coros-backup."""

import sys
import logging
from pathlib import Path
from getpass import getpass
from typing import Optional

import click

from corosexport.client import CorosClient, CorosAuthError, CorosAPIError
from corosexport.backup import BackupManager
from corosexport.models import ExportFormat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--backup-dir",
    type=click.Path(file_okay=False, writable=True),
    default="./coros_activities",
    help="Directory to store backed up activities",
)
@click.option(
    "--email",
    prompt="Coros email",
    help="Coros account email",
)
@click.option(
    "--password",
    prompt=False,
    hide_input=True,
    default=None,
    help="Coros account password (prompts if not provided)",
)
@click.option(
    "--format",
    multiple=True,
    type=click.Choice(["fit", "tcx", "gpx", "json"], case_sensitive=False),
    default=["fit", "tcx"],
    help="Export formats to download (can be used multiple times)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    backup_dir: str,
    email: str,
    password: Optional[str],
    format: tuple[str],
    verbose: bool,
) -> int:
    """Backup Coros activities to local disk.
    
    This tool performs incremental backups of your Coros Training Hub activities.
    On first run, it downloads all activities. On subsequent runs, it only downloads
    new activities not already in the backup directory.
    
    Example:
        coros-backup --backup-dir=./my_activities
    """
    
    if verbose:
        logging.getLogger("corosexport").setLevel(logging.DEBUG)
    
    # Get password if not provided
    if not password:
        password = getpass("Coros password: ")
    
    if not password:
        click.echo("Error: Password is required", err=True)
        return 1
    
    # Convert format strings to ExportFormat enums
    try:
        formats = [ExportFormat(fmt.lower()) for fmt in format]
    except ValueError as e:
        click.echo(f"Error: Invalid format - {e}", err=True)
        return 1
    
    # Create client and authenticate
    try:
        click.echo("Authenticating with Coros...")
        client = CorosClient(email=email, password=password)
        client.authenticate()
    except CorosAuthError as e:
        click.echo(f"Authentication failed: {e}", err=True)
        return 1
    
    # Run backup
    try:
        backup_manager = BackupManager(
            client=client,
            backup_dir=Path(backup_dir),
            formats=formats,
        )
        
        click.echo(f"Starting backup to {backup_dir}...")
        stats = backup_manager.run_backup()
        
        # Print summary
        click.echo("\n" + "=" * 60)
        click.echo("Backup Summary")
        click.echo("=" * 60)
        click.echo(f"Activities found:     {stats['activities_found']}")
        click.echo(f"  - Downloaded:       {stats['activities_downloaded']}")
        click.echo(f"  - Skipped (cached): {stats['activities_skipped']}")
        click.echo(f"  - Failed:           {stats['activities_failed']}")
        
        if stats.get("formats_downloaded"):
            click.echo("\nFormats downloaded:")
            for fmt, count in stats["formats_downloaded"].items():
                click.echo(f"  - {fmt.upper()}: {count} files")
        
        click.echo("=" * 60)
        
        return 0
        
    except CorosAPIError as e:
        click.echo(f"Backup failed: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
