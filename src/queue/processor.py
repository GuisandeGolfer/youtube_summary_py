"""
Queue Processor - Parallel processing of video queue

This module handles the actual processing of videos in the queue.
It processes multiple videos in parallel (2 workers) to speed up
the overall processing time.
"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable

# Import queue manager components
from .manager import VideoQueue, QueueItem, VideoStatus

# Import core processing functions
from src.core.youtube import download_video_audio, get_video_info
from src.core.transcription import transcribe_audio_file
from src.core.summarization import generate_summary
from src.core.database import save_transcription_to_db

logger = logging.getLogger(__name__)


class QueueProcessor:
    """
    Processes videos in the queue using parallel workers.

    This class manages the parallel processing of multiple videos,
    with progress tracking and error handling.
    """

    def __init__(
        self,
        queue: VideoQueue,
        audio_path: str,
        db_path: str,
        max_workers: int = 2,
        on_progress_callback: Optional[Callable] = None
    ):
        """
        Initialize the queue processor.

        Args:
            queue: VideoQueue instance to process
            audio_path: Directory to store audio files
            db_path: Path to SQLite database
            max_workers: Number of parallel workers (default: 2)
            on_progress_callback: Optional callback function called on progress updates
        """
        self.queue = queue
        self.audio_path = audio_path
        self.db_path = db_path
        self.max_workers = max_workers
        self.on_progress = on_progress_callback
        self.should_stop = False

        # Ensure audio directory exists
        os.makedirs(self.audio_path, exist_ok=True)

    def process_queue_parallel(self):
        """
        Process all pending videos in the queue using parallel workers.

        This method processes up to max_workers videos simultaneously.
        Videos are processed in the order they appear in the queue.

        Returns:
            dict: Summary of processing results
        """
        logger.info(f"Starting parallel queue processing with {self.max_workers} workers")

        # Mark queue as processing
        self.queue.is_processing = True
        self.should_stop = False

        # Get all pending items
        pending_items = self.queue.get_pending_items()

        if not pending_items:
            logger.warning("No pending items in queue")
            self.queue.is_processing = False
            return {
                'completed': 0,
                'failed': 0,
                'skipped': 0,
                'total': 0
            }

        logger.info(f"Processing {len(pending_items)} videos")

        # Track results
        completed = 0
        failed = 0

        # Process videos in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all pending items to the executor
            future_to_item = {
                executor.submit(self._process_single_video, item): item
                for item in pending_items
            }

            # Update active worker count
            self.queue.active_workers = len(future_to_item)

            # Process results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]

                # Check if we should stop
                if self.should_stop:
                    logger.info("Stop requested, cancelling remaining tasks")
                    # Cancel pending futures
                    for f in future_to_item:
                        f.cancel()
                    break

                try:
                    # Get result (will raise exception if processing failed)
                    success = future.result()

                    if success:
                        completed += 1
                        logger.info(f"✓ Completed: {item.title or item.url}")
                    else:
                        failed += 1
                        logger.error(f"✗ Failed: {item.title or item.url}")

                except Exception as e:
                    failed += 1
                    logger.error(f"✗ Exception processing {item.url}: {str(e)}")

                # Update active worker count
                self.queue.active_workers = len([f for f in future_to_item if not f.done()])

        # Mark queue as done processing
        self.queue.is_processing = False
        self.queue.active_workers = 0

        # Return summary
        results = {
            'completed': completed,
            'failed': failed,
            'skipped': 0,
            'total': len(pending_items)
        }

        logger.info(
            f"Queue processing complete: "
            f"{completed} completed, {failed} failed, "
            f"{len(pending_items)} total"
        )

        return results

    def _process_single_video(self, item: QueueItem) -> bool:
        """
        Process a single video through all stages.

        This method is run in parallel for multiple videos.

        Stages:
        0. Fetch video info (get title)
        1. Download (0-25%)
        2. Transcribe (25-75%)
        3. Summarize (75-95%)
        4. Save to database (95-100%)

        Args:
            item: QueueItem to process

        Returns:
            bool: True if successful, False if failed
        """
        try:
            logger.info(f"Starting processing: {item.url}")

            # STAGE 0: Fetch video info to get title
            try:
                self._update_progress(item, 1, "Fetching video info...")
                video_info = get_video_info(item.url)
                item.title = video_info['title']
                item.duration = video_info['duration']
                self._update_progress(item, 3, f"Found: {item.title}")
                logger.info(f"Video title: {item.title}")
            except Exception as e:
                logger.warning(f"Could not fetch video info: {str(e)}")
                # Continue anyway, title will be set from filename

            # Check for stop signal
            if self.should_stop:
                item.status = VideoStatus.PENDING
                return False

            # STAGE 1: Download (0-25%)
            item.status = VideoStatus.DOWNLOADING
            self._update_progress(item, 5, "Starting download...")

            filename = download_video_audio(item.url, self.audio_path)

            # Use video title if we have it, otherwise use filename
            if not item.title:
                item.title = filename

            self._update_progress(item, 25, "Download complete")

            # Check for stop signal
            if self.should_stop:
                item.status = VideoStatus.PENDING
                return False

            # STAGE 2: Transcribe (25-75%)
            item.status = VideoStatus.TRANSCRIBING
            self._update_progress(item, 30, "Starting transcription...")

            transcription = transcribe_audio_file(filename, self.audio_path)

            self._update_progress(item, 75, "Transcription complete")

            # Check for stop signal
            if self.should_stop:
                item.status = VideoStatus.PENDING
                return False

            # STAGE 3: Summarize (75-95%)
            item.status = VideoStatus.SUMMARIZING
            self._update_progress(item, 80, "Generating summary...")

            summary = generate_summary(transcription, item.url)

            self._update_progress(item, 95, "Summary complete")

            # STAGE 4: Save to database (95-100%)
            self._update_progress(item, 98, "Saving to database...")

            save_transcription_to_db(
                db_path=self.db_path,
                transcription=transcription,
                video_url=item.url,
                summary=summary
            )

            # Mark as completed
            item.status = VideoStatus.COMPLETED
            item.progress = 100
            item.current_step = "Complete!"
            self._notify_progress(item)

            logger.info(f"✓ Successfully processed: {item.title}")
            return True

        except Exception as e:
            # Mark as failed with error message
            item.status = VideoStatus.FAILED
            item.error = str(e)
            item.current_step = f"Failed: {str(e)[:50]}"
            self._notify_progress(item)

            logger.error(f"✗ Failed to process {item.url}: {str(e)}")
            return False

    def _update_progress(self, item: QueueItem, progress: int, step: str):
        """
        Update progress for a queue item.

        Args:
            item: QueueItem to update
            progress: Progress percentage (0-100)
            step: Human-readable description of current step
        """
        item.progress = progress
        item.current_step = step
        self._notify_progress(item)

    def _notify_progress(self, item: QueueItem):
        """
        Notify callback about progress update (if callback is set).

        Args:
            item: QueueItem that was updated
        """
        if self.on_progress:
            try:
                self.on_progress(item)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    def stop(self):
        """
        Request to stop processing the queue.

        This will stop after the current videos finish processing.
        It does not forcefully kill threads.
        """
        logger.info("Stop requested")
        self.should_stop = True

    def get_status(self) -> dict:
        """
        Get current processing status.

        Returns:
            dict: Status information including active workers and progress
        """
        return {
            'is_processing': self.queue.is_processing,
            'active_workers': self.queue.active_workers,
            'pending_count': len(self.queue.get_pending_items()),
            'active_count': len(self.queue.get_active_items()),
            'completed_count': self.queue.get_completed_count(),
            'failed_count': self.queue.get_failed_count(),
            'total_count': self.queue.get_total_count()
        }
