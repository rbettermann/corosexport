"""Data models for Coros activities and metadata."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# Mapping from Coros sport type codes to ActivityType string names
_SPORT_TYPE_MAP = {
    100: "RUNNING",
    101: "TRAIL_RUNNING",
    200: "CYCLING",
    201: "MOUNTAIN_BIKING",
    300: "SWIMMING",
    301: "POOL_SWIM",
    104: "HIKING",
    402: "STRENGTH",
    904: "YOGA",
    500: "TRIATHLON",
}

_FILE_TYPE_MAP = {
    0: "csv",
    1: "gpx",
    2: "kml",
    3: "tcx",
    4: "fit",
}

class ActivityType(str, Enum):
    """Supported Coros activity types (using Coros sport type codes)."""
    RUNNING = "RUNNING"
    TRAIL_RUNNING = "TRAIL_RUNNING"
    CYCLING = "CYCLING"
    MOUNTAIN_BIKING = "MOUNTAIN_BIKING"
    SWIMMING = "SWIMMING"
    POOL_SWIM = "POOL_SWIM"
    HIKING = "HIKING"
    STRENGTH = "STRENGTH"
    YOGA = "YOGA"
    TRIATHLON = "TRIATHLON"
    OTHER = "OTHER"
    
    @classmethod
    def from_sport_type(cls, sport_type: int) -> "ActivityType":
        type_name = _SPORT_TYPE_MAP.get(sport_type, "OTHER")
        return cls(type_name)
    
    def to_sport_type(self) -> Optional[int]:
        for code, name in _SPORT_TYPE_MAP.items():
            if name == self.value:
                return code
        return None
    
    @classmethod
    def _missing_(cls, value):
        """Return OTHER for unknown activity types."""
        return cls.OTHER

class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    GPX = "gpx"
    KML = "kml"
    TCX = "tcx"
    FIT = "fit"

    @classmethod
    def from_file_type(cls, sport_type: int) -> "ActivityType":
        type_name = _FILE_TYPE_MAP.get(sport_type, "OTHER")
        return cls(type_name)
    
    def to_file_type(self) -> Optional[int]:
        for code, name in _FILE_TYPE_MAP.items():
            if name == self.value:
                return code
        return None


class ActivitySummary(BaseModel):
    """Summary metadata of a Coros activity."""
    activity_id: str = Field(..., description="Unique activity identifier")
    activity_name: str = Field(..., description="Name/title of the activity")
    activity_type: ActivityType = Field(..., description="Type of activity")
    start_time: datetime = Field(..., description="When the activity started (UTC)")
    end_time: datetime = Field(..., description="When the activity started (UTC)")
    workout_seconds: int = Field(..., description="Activity duration in seconds")
    total_seconds: int = Field(..., description="Activity duration in seconds")
    distance_meters: float = Field(..., description="Total distance in meters")
    
    class Config:
        use_enum_values = False


class Activity(BaseModel):
    """Complete activity data with details."""
    summary: ActivitySummary
    
    # Detailed metrics
    avg_cadence: Optional[int] = Field(None, description="Average cadence (steps/min for running)")
    max_cadence: Optional[int] = Field(None, description="Max cadence")
    avg_power: Optional[float] = Field(None, description="Average power (watts, cycling)")
    max_power: Optional[float] = Field(None, description="Max power (watts)")
    total_ascent: Optional[float] = Field(None, description="Total elevation ascent")
    
    # Raw data (if available)
    gps_points: Optional[list] = Field(None, description="GPS trackpoints (lat, lon, alt, time)")
    heart_rate_samples: Optional[list] = Field(None, description="HR sample data")
    
    class Config:
        use_enum_values = False


class BackupState(BaseModel):
    """State information for incremental backups."""
    last_backup_timestamp: datetime = Field(
        ...,
        description="When the last backup completed"
    )
    total_activities_backed_up: int = Field(
        default=0,
        description="Total activities successfully backed up"
    )
    last_synced_activity_id: Optional[str] = Field(
        None,
        description="Most recent activity ID from last backup"
    )
    downloaded_activity_ids: set[str] = Field(
        default_factory=set,
        description="Set of all activity IDs already downloaded"
    )
    
    class Config:
        arbitrary_types_allowed = True
