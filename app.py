import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from youtube import download_video_audio
from transcription import transcribe_audio_file
from summarization import generate_summary
from database import save_transcription_to_db

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

# Constants
AUDIO_PATH = os.path.join(os.path.dirname(__file__), "audio")
DB_PATH = os.path.join(os.path.dirname(__file__), "transcriptions.db")

# Ensure directories exist
os.makedirs(AUDIO_PATH, exist_ok=True)


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


if __name__ == '__main__':
    print("\n" + "="*50)
    print("YouTube Video Summarizer")
    print("="*50)
    print("\nServer starting...")
    print("Open your browser and go to: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
