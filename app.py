import logging
import threading
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Import configuration
from config import AUDIO_PATH, DB_PATH_STR, FLASK_HOST, FLASK_PORT, FLASK_DEBUG, QUEUE_MAX_WORKERS

# Import core functionality
from src.core import (
    download_video_audio,
    transcribe_audio_file,
    generate_summary,
    save_transcription_to_db
)

# Import queue management
from src.queue import VideoQueue, QueueProcessor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Use DB_PATH from config
DB_PATH = DB_PATH_STR

# Queue instances (global)
video_queue = VideoQueue()
queue_processor = None


@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_video():
    """Process a YouTube video URL"""
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        logger.info(f"Processing video: {url}")

        # Step 1: Download audio
        logger.info("Downloading audio...")
        filename = download_video_audio(url, AUDIO_PATH)

        # Step 2: Transcribe audio
        logger.info("Transcribing audio...")
        transcription = transcribe_audio_file(filename, AUDIO_PATH)

        # Step 3: Generate summary
        logger.info("Generating summary...")
        summary = generate_summary(transcription, url)

        # Step 4: Save to database
        logger.info("Saving to database...")
        save_transcription_to_db(
            db_path=DB_PATH,
            transcription=transcription,
            video_url=url,
            summary=summary
        )

        logger.info("Process completed successfully")

        return jsonify({
            'success': True,
            'summary': summary,
            'message': 'Video processed successfully! Transcription saved to database.'
        })

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# QUEUE ROUTES
# ============================================================================

@app.route('/queue/add', methods=['POST'])
def add_to_queue():
    """
    Add a video URL to the processing queue.

    Request JSON:
        {
            "url": "https://youtube.com/watch?v=..."
        }

    Returns:
        JSON with the created queue item
    """
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Add to queue
        item = video_queue.add(url)

        # Fetch video info (title) in background to avoid blocking
        # This makes the title appear immediately in the queue UI
        try:
            from src.core.youtube import get_video_info
            video_info = get_video_info(url)
            item.title = video_info['title']
            item.duration = video_info['duration']
            logger.info(f"Added to queue: {item.title} (ID: {item.id})")
        except Exception as e:
            logger.warning(f"Could not fetch video info for {url}: {str(e)}")
            logger.info(f"Added to queue: {url} (ID: {item.id})")

        return jsonify({
            'success': True,
            'item': item.to_dict()
        })

    except Exception as e:
        logger.error(f"Error adding to queue: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/queue/list', methods=['GET'])
def list_queue():
    """
    Get the current state of the queue.

    Returns:
        JSON with all queue items and processing status
    """
    try:
        return jsonify(video_queue.to_dict())

    except Exception as e:
        logger.error(f"Error listing queue: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/queue/start', methods=['POST'])
def start_queue():
    """
    Start processing the queue in the background.

    This runs the QueueProcessor in a separate thread so it doesn't
    block the Flask server.

    Returns:
        JSON indicating processing has started
    """
    global queue_processor

    try:
        # Check if already processing
        if video_queue.is_processing:
            return jsonify({
                'error': 'Queue is already processing'
            }), 400

        # Check if there are pending items
        pending_items = video_queue.get_pending_items()
        if not pending_items:
            return jsonify({
                'error': 'No pending items in queue'
            }), 400

        logger.info(f"Starting queue processing with {len(pending_items)} items")

        # Create processor instance
        queue_processor = QueueProcessor(
            queue=video_queue,
            audio_path=AUDIO_PATH,
            db_path=DB_PATH,
            max_workers=QUEUE_MAX_WORKERS
        )

        # Run processor in background thread
        def run_processor():
            try:
                results = queue_processor.process_queue_parallel()
                logger.info(f"Queue processing complete: {results}")
            except Exception as e:
                logger.error(f"Error in queue processing: {str(e)}", exc_info=True)

        thread = threading.Thread(target=run_processor, daemon=True)
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Queue processing started',
            'pending_count': len(pending_items)
        })

    except Exception as e:
        logger.error(f"Error starting queue: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/queue/remove/<item_id>', methods=['DELETE'])
def remove_from_queue(item_id):
    """
    Remove an item from the queue by ID.

    Args:
        item_id: ID of the queue item to remove

    Returns:
        JSON indicating success or failure
    """
    try:
        # Don't allow removing items while processing
        if video_queue.is_processing:
            return jsonify({
                'error': 'Cannot remove items while queue is processing'
            }), 400

        success = video_queue.remove(item_id)

        if success:
            logger.info(f"Removed item from queue: {item_id}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Item not found'}), 404

    except Exception as e:
        logger.error(f"Error removing from queue: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/queue/clear', methods=['POST'])
def clear_queue():
    """
    Clear all items from the queue.

    Returns:
        JSON indicating success
    """
    try:
        # Don't allow clearing while processing
        if video_queue.is_processing:
            return jsonify({
                'error': 'Cannot clear queue while processing'
            }), 400

        video_queue.clear()
        logger.info("Queue cleared")

        return jsonify({
            'success': True,
            'message': 'Queue cleared'
        })

    except Exception as e:
        logger.error(f"Error clearing queue: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# END QUEUE ROUTES
# ============================================================================


if __name__ == '__main__':
    print("\n" + "="*50)
    print("YouTube Video Summarizer")
    print("="*50)
    print("\nServer starting...")
    print(f"Open your browser and go to: http://localhost:{FLASK_PORT}")
    print("\nPress Ctrl+C to stop the server")
    print("="*50 + "\n")

    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
