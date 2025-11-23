"""
Queue management for batch video processing.

This package contains:
- VideoQueue: Queue data structure and management
- QueueProcessor: Parallel processing of queued videos
"""

from .manager import VideoQueue, QueueItem, VideoStatus
from .processor import QueueProcessor

__all__ = [
    'VideoQueue',
    'QueueItem',
    'VideoStatus',
    'QueueProcessor',
]
