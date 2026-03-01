"""Backup manager for incremental activity downloads."""

import json
import logging
from pathlib import Path
from typing import Optional, Set
from datetime import datetime

from corosexport.client import CorosClient, CorosAPIError
from corosexport.models import BackupState, ActivitySummary, ExportFormat

logger = logging.getLogger(__name__)

STATE_FILE_NAME = ".corosexport_state.json"


class BackupManager:
    """Manages incremental backups of Coros activities."""
    
    def __init__(
        self,
        client: CorosClient,
        backup_dir: Path,
        formats: Optional[list[ExportFormat]] = None,
    ):
        """Initialize backup manager.
        
        Args:
            client: Authenticated Coros API client
            backup_dir: Directory to store backed up activities
            formats: List of export formats (default: [FIT, TCX])
        """
        self.client = client
        self.backup_dir = Path(backup_dir)
        self.formats = formats or [ExportFormat.FIT, ExportFormat.TCX]
        self.state_file = self.backup_dir / STATE_FILE_NAME
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self.state = self._load_state()
    
    def _load_state(self) -> BackupState:
        """Load backup state from disk.
        
        Returns:
            BackupState object (new or loaded from file)
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    # Reconstruct BackupState with proper date parsing
                    state = BackupState(
                        last_backup_timestamp=datetime.fromisoformat(
                            data["last_backup_timestamp"]
                        ),
                        total_activities_backed_up=data.get("total_activities_backed_up", 0),
                        last_synced_activity_id=data.get("last_synced_activity_id"),
                        downloaded_activity_ids=set(data.get("downloaded_activity_ids", [])),
                    )
                    logger.info(f"Loaded backup state with {len(state.downloaded_activity_ids)} activities")
                    return state
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load state file: {e}. Starting fresh.")
        
        # Create new state
        return BackupState(
            last_backup_timestamp=datetime.now(),
            total_activities_backed_up=0,
            downloaded_activity_ids=set(),
        )
    
    def _save_state(self) -> None:
        """Save backup state to disk."""
        try:
            data = {
                "last_backup_timestamp": self.state.last_backup_timestamp.isoformat(),
                "total_activities_backed_up": self.state.total_activities_backed_up,
                "last_synced_activity_id": self.state.last_synced_activity_id,
                "downloaded_activity_ids": list(self.state.downloaded_activity_ids),
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug("Backup state saved")
        except IOError as e:
            logger.error(f"Failed to save state file: {e}")
    
    def run_backup(self) -> dict:
        """Run an incremental backup of all activities.
        
        Returns:
            Dictionary with backup statistics
        """
        logger.info("Starting backup")
        global stats
        stats = {
            "activities_found": 0,
            "activities_skipped": 0,
            "activities_downloaded": 0,
            "activities_failed": 0,
            "formats_downloaded": {},
        }
        
        try:
            all_activities = self.client.get_activities(limit=200)
            stats["activities_found"] = len(all_activities)
            
            logger.info(f"Found {len(all_activities)} total activities")
            
            for activity in all_activities:
                if activity.activity_id in self.state.downloaded_activity_ids:
                    logger.debug(f"Skipping already-backed-up activity {activity.activity_id}")
                    stats["activities_skipped"] += 1
                    continue
                
                if self._download_activity_files(activity):
                    self.state.downloaded_activity_ids.add(activity.activity_id)
                    self.state.last_synced_activity_id = activity.activity_id
                    self.state.total_activities_backed_up += 1
                    stats["activities_downloaded"] += 1
                else:
                    stats["activities_failed"] += 1
            
            # Update backup timestamp and save state
            self.state.last_backup_timestamp = datetime.now()
            self._save_state()
            
            logger.info(f"Backup completed: {stats['activities_downloaded']} new, "
                       f"{stats['activities_skipped']} skipped, {stats['activities_failed']} failed")
            
            return stats
            
        except CorosAPIError as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def _download_activity_files(self, activity: ActivitySummary) -> bool:
        """Download and save activity files.
        
        Args:
            activity: Activity to download
            
        Returns:
            True if at least one file was downloaded successfully
        """
        success = False

        self.backup_dir.mkdir(parents=True, exist_ok=True)
  
        filename_prefix = self.backup_dir / f"{activity.start_time.strftime('%Y-%m-%d')}_{activity.activity_id}"
        
        metadata_file = f"{filename_prefix}-metadata.json"
        try:
            with open(metadata_file, "w") as f:
                json.dump(activity.model_dump(mode="json"), f, indent=2, default=str)
            logger.debug(f"Saved metadata to {metadata_file}")
        except IOError as e:
            logger.warning(f"Failed to save metadata: {e}")
        
        # Download activity in each requested format
        for fmt in self.formats:            
            file_ext = fmt.value
            output_file = f"{filename_prefix}.{file_ext}"
            
            try:
                self.client.download_activity_file(
                    activity.activity_id,
                    activity.activity_type,
                    fmt,
                    str(output_file),
                )
                logger.info(f"Downloaded {fmt.value} for {activity.activity_id}")
                success = True
                
                if fmt.value not in stats["formats_downloaded"]:
                    stats["formats_downloaded"][fmt.value] = 0
                stats["formats_downloaded"][fmt.value] += 1
                
            except CorosAPIError as e:
                logger.warning(f"Failed to download {fmt.value}: {e}")
        
        return success
    
    def get_backup_stats(self) -> dict:
        """Get current backup statistics.
        
        Returns:
            Dictionary with backup info
        """
        return {
            "last_backup": self.state.last_backup_timestamp.isoformat(),
            "total_activities": self.state.total_activities_backed_up,
            "downloaded_ids_count": len(self.state.downloaded_activity_ids),
        }
