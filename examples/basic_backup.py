"""Example usage of corosexport as a library.

This demonstrates how to use the Coros exporter programmatically
in your own Python code.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta

from corosexport import CorosClient, BackupManager
from corosexport.models import ExportFormat, ActivityType

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def example_basic_backup():
    """Simple backup example."""
    print("Example 1: Basic Backup")
    print("-" * 60)
    
    # Create client with credentials
    client = CorosClient(
        email="your_email@example.com",
        password="your_password",
    )
    
    # Authenticate
    print("Authenticating...")
    client.authenticate()
    print("✓ Successfully authenticated\n")
    
    # Create backup manager
    backup_manager = BackupManager(
        client=client,
        backup_dir=Path("./coros_activities"),
        formats=[ExportFormat.FIT, ExportFormat.TCX],
    )
    
    # Run backup
    print("Starting backup...")
    stats = backup_manager.run_backup()
    
    print(f"\nBackup complete!")
    print(f"  Found: {stats['activities_found']} activities")
    print(f"  Downloaded: {stats['activities_downloaded']} new")
    print(f"  Skipped: {stats['activities_skipped']} (already have)")
    print(f"  Failed: {stats['activities_failed']}")


def example_custom_formats():
    """Example with custom export formats."""
    print("\n\nExample 2: Custom Export Formats")
    print("-" * 60)
    
    client = CorosClient(
        email="your_email@example.com",
        password="your_password",
    )
    client.authenticate()
    
    # Only backup as FIT files
    backup_manager = BackupManager(
        client=client,
        backup_dir=Path("./fit_only"),
        formats=[ExportFormat.FIT],  # Only FIT format
    )
    
    stats = backup_manager.run_backup()
    print(f"Downloaded {stats['activities_downloaded']} activities as FIT")


def example_activity_filtering():
    """Example showing how to filter and inspect activities."""
    print("\n\nExample 3: Activity Filtering and Inspection")
    print("-" * 60)
    
    client = CorosClient(
        email="your_email@example.com",
        password="your_password",
    )
    client.authenticate()
    
    # Get all activities
    all_activities = client.get_activities(limit=1000)
    print(f"Total activities: {len(all_activities)}\n")
    
    # Filter for running activities in the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_runs = [
        a for a in all_activities
        if (a.activity_type == ActivityType.RUNNING and 
            a.start_time > thirty_days_ago)
    ]
    
    print(f"Running activities in last 30 days: {len(recent_runs)}\n")
    
    # Print summary of each
    for activity in sorted(recent_runs, key=lambda a: a.start_time, reverse=True):
        duration_min = activity.duration_seconds // 60
        pace_min = activity.avg_pace_sec_per_km // 60 if activity.avg_pace_sec_per_km else 0
        pace_sec = int(activity.avg_pace_sec_per_km % 60) if activity.avg_pace_sec_per_km else 0
        
        print(f"{activity.start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"  {activity.activity_name}")
        print(f"  Distance: {activity.distance_meters/1000:.2f}km")
        print(f"  Duration: {duration_min} minutes")
        print(f"  Pace: {pace_min}:{pace_sec:02d} /km")
        if activity.avg_heart_rate:
            print(f"  Avg HR: {activity.avg_heart_rate} bpm")
        print()


def example_get_activity_details():
    """Example of fetching detailed activity information."""
    print("\n\nExample 4: Get Activity Details")
    print("-" * 60)
    
    client = CorosClient(
        email="your_email@example.com",
        password="your_password",
    )
    client.authenticate()
    
    # Get first activity
    activities = client.get_activities(limit=1)
    
    if activities:
        activity = activities[0]
        print(f"Activity: {activity.activity_name}")
        print(f"ID: {activity.activity_id}\n")
        
        # Fetch detailed information
        details = client.get_activity_detail(activity.activity_id)
        
        # Download the activity
        print(f"\nDownloading {activity.activity_id} as FIT...")
        output_file = f"/tmp/activity_{activity.activity_id}.fit"
        client.download_activity_file(
            activity.activity_id,
            ExportFormat.FIT,
            output_file,
        )
        print(f"✓ Saved to {output_file}")


def example_backup_status():
    """Example showing how to check backup status."""
    print("\n\nExample 5: Backup Status Check")
    print("-" * 60)
    
    client = CorosClient(
        email="your_email@example.com",
        password="your_password",
    )
    client.authenticate()
    
    backup_manager = BackupManager(
        client=client,
        backup_dir=Path("./coros_activities"),
    )
    
    # Check current backup status
    stats = backup_manager.get_backup_stats()
    
    print(f"Backup Directory: {backup_manager.backup_dir}")
    print(f"Last Backup: {stats['last_backup']}")
    print(f"Total Backed Up: {stats['total_activities']} activities")
    print(f"State Entries: {stats['downloaded_ids_count']} unique IDs")
    
    # Show activities already downloaded
    print(f"\nAlready backed up (first 5):")
    for activity_id in list(backup_manager.state.downloaded_activity_ids)[:5]:
        print(f"  - {activity_id}")


def example_format_selection():
    """Example of different format selection strategies."""
    print("\n\nExample 6: Format Selection Strategies")
    print("-" * 60)
    
    client = CorosClient(
        email="your_email@example.com",
        password="your_password",
    )
    client.authenticate()
    
    # Strategy 1: All formats (complete backup)
    print("Strategy 1: Download all formats")
    all_formats = [
        ExportFormat.FIT,
        ExportFormat.TCX,
        ExportFormat.GPX,
        ExportFormat.JSON,
    ]
    backup_all = BackupManager(
        client=client,
        backup_dir=Path("./complete_backup"),
        formats=all_formats,
    )
    print(f"  Formats: {', '.join(f.value for f in all_formats)}\n")
    
    # Strategy 2: Minimal backup (just FIT for device sync)
    print("Strategy 2: Minimal backup (FIT only)")
    backup_fit = BackupManager(
        client=client,
        backup_dir=Path("./fit_only"),
        formats=[ExportFormat.FIT],
    )
    print(f"  Formats: FIT\n")
    
    # Strategy 3: Analysis-friendly (TCX + JSON for tools)
    print("Strategy 3: Analysis-friendly (TCX + JSON)")
    backup_analysis = BackupManager(
        client=client,
        backup_dir=Path("./analysis_backup"),
        formats=[ExportFormat.TCX, ExportFormat.JSON],
    )
    print(f"  Formats: TCX, JSON\n")


def example_error_handling():
    """Example showing proper error handling."""
    print("\n\nExample 7: Error Handling")
    print("-" * 60)
    
    from corosexport.client import CorosAuthError, CorosAPIError
    
    try:
        # Try to authenticate with wrong credentials
        client = CorosClient(
            email="wrong@example.com",
            password="wrong_password",
        )
        client.authenticate()
        
    except CorosAuthError as e:
        print(f"✗ Authentication failed: {e}")
        print("  → Check your email and password\n")
    
    try:
        # Assume authentication succeeded, try to backup
        client = CorosClient(
            email="your_email@example.com",
            password="your_password",
        )
        client.authenticate()
        
        backup_manager = BackupManager(
            client=client,
            backup_dir=Path("./readonly_directory"),
            formats=[ExportFormat.FIT],
        )
        
        # This would fail if directory is not writable
        stats = backup_manager.run_backup()
        
    except CorosAPIError as e:
        print(f"✗ API error during backup: {e}")
        print("  → Check your internet connection and try again\n")
    except PermissionError as e:
        print(f"✗ Permission error: {e}")
        print("  → Check that the backup directory is writable\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Corosexport - Library Usage Examples")
    print("=" * 60)
    print("\nNote: These examples require valid Coros credentials.")
    print("Update the email/password in each function before running.\n")
    
    # Uncomment the example you want to run:
    
    # example_basic_backup()
    # example_custom_formats()
    # example_activity_filtering()
    # example_get_activity_details()
    # example_backup_status()
    # example_format_selection()
    # example_error_handling()
    
    print("\nTo run an example, uncomment it in the 'if __name__' block")
    print("and update the credentials.")
