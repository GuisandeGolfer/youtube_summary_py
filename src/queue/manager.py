"""
Queue Manager - Data structures for managing video processing queue

This module provides the core data structures for queueing multiple
YouTube videos for processing. It does not handle the actual processing,
just the queue management.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime
import uuid


class VideoStatus(Enum):
    """Status of a video in the queue"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueueItem:
    """
    Represents a single video in the processing queue.

    Attributes:
        id: Unique identifier for this queue item
        url: YouTube video URL
        status: Current processing status
        progress: Processing progress (0-100%)
        current_step: Human-readable description of current step
        error: Error message if status is FAILED
        title: Video title (populated after download)
        duration: Video duration in seconds (populated after download)
        added_at: Timestamp when item was added to queue
    """
    url: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: VideoStatus = VideoStatus.PENDING
    progress: int = 0
    current_step: str = "Waiting in queue..."
    error: Optional[str] = None
    title: str = ""
    duration: int = 0
    added_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'url': self.url,
            'status': self.status.value,
            'progress': self.progress,
            'current_step': self.current_step,
            'error': self.error,
            'title': self.title,
            'duration': self.duration,
            'added_at': self.added_at.isoformat()
        }


class VideoQueue:
    """
    Manages a queue of videos to be processed.

    This class handles adding, removing, and tracking videos in the queue.
    It does NOT handle the actual processing - that's done by QueueProcessor.
    """

    def __init__(self):
        """Initialize an empty queue"""
        self.items: List[QueueItem] = []
        self.is_processing: bool = False
        self.active_workers: int = 0

    def add(self, url: str) -> QueueItem:
        """
        Add a video URL to the queue.

        Args:
            url: YouTube video URL

        Returns:
            QueueItem: The created queue item
        """
        item = QueueItem(url=url)
        self.items.append(item)
        return item

    def remove(self, item_id: str) -> bool:
        """
        Remove a video from the queue by ID.

        Args:
            item_id: ID of the item to remove

        Returns:
            bool: True if item was found and removed, False otherwise
        """
        original_length = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        return len(self.items) < original_length

    def clear(self):
        """Remove all items from the queue"""
        self.items = []

    def get_by_id(self, item_id: str) -> Optional[QueueItem]:
        """
        Get a queue item by ID.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            QueueItem or None if not found
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def get_pending_items(self) -> List[QueueItem]:
        """
        Get all pending (not yet processed) items.

        Returns:
            List of QueueItem with PENDING status
        """
        return [item for item in self.items if item.status == VideoStatus.PENDING]

    def get_active_items(self) -> List[QueueItem]:
        """
        Get all items currently being processed.

        Returns:
            List of QueueItem with DOWNLOADING, TRANSCRIBING, or SUMMARIZING status
        """
        active_statuses = {
            VideoStatus.DOWNLOADING,
            VideoStatus.TRANSCRIBING,
            VideoStatus.SUMMARIZING
        }
        return [item for item in self.items if item.status in active_statuses]

    def get_completed_count(self) -> int:
        """Get number of completed items"""
        return sum(1 for item in self.items if item.status == VideoStatus.COMPLETED)

    def get_failed_count(self) -> int:
        """Get number of failed items"""
        return sum(1 for item in self.items if item.status == VideoStatus.FAILED)

    def get_total_count(self) -> int:
        """Get total number of items in queue"""
        return len(self.items)

    def to_dict(self) -> dict:
        """
        Convert queue to dictionary for JSON serialization.

        Returns:
            Dictionary containing queue state and all items
        """
        return {
            'items': [item.to_dict() for item in self.items],
            'is_processing': self.is_processing,
            'active_workers': self.active_workers,
            'stats': {
                'total': self.get_total_count(),
                'completed': self.get_completed_count(),
                'failed': self.get_failed_count(),
                'pending': len(self.get_pending_items()),
                'active': len(self.get_active_items())
            }
        }
