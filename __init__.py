"""Corosexport - Coros Activity Exporter.

A library and tool for downloading/backing up Coros activities.
"""

__version__ = "0.1.0"
__author__ = "Ralf Bettermann"
__license__ = "Apache-2.0"

from corosexport.client import CorosClient
from corosexport.backup import BackupManager
from corosexport.models import Activity, ActivitySummary

__all__ = [
    "CorosClient",
    "BackupManager",
    "Activity",
    "ActivitySubackup.pymmary",
]
