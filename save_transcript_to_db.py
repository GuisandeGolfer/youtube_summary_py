import os
import sqlite3
from yt_dlp import YoutubeDL

class NewFileHandler:
    def __init__(self, db_path, transcription_txt, video_url):
        self.db_path = db_path
        self.transcription_txt = transcription_txt
        self.video_url = video_url

    def insert_transcription_into_db(self):
        # Extract video information using yt-dlp
        ydl_opts = {}
        with YoutubeDL(ydl_opts) as ydl:
            try:
                video_info = ydl.extract_info(self.video_url, download=False)
            except Exception as e:
                print(f"Error extracting video info: {e}")
                return

        # Connect to the database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return

        # Check if the 'videos' table exists
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='videos';
            """)
            table_exists = cursor.fetchone()
            if table_exists:
                print("Table 'videos' already exists.")
                # Optional: Verify schema or perform migrations here
                # Example: self.verify_table_schema(cursor)
            else:
                print("Table 'videos' does not exist. Creating table.")
                cursor.execute('''
                    CREATE TABLE videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        url TEXT,
                        video_length INTEGER,
                        channel TEXT,
                        transcription TEXT
                    )
                ''')
                print("Table 'videos' created successfully.")
        except Exception as e:
            print(f"Error checking or creating table: {e}")
            conn.close()
            return

        # Prepare data for insertion
        title = video_info.get('title', 'Unknown Title')
        url = video_info.get('webpage_url', self.video_url)
        video_length = video_info.get('duration', 0)
        channel = video_info.get('uploader', 'Unknown Channel')

        # Insert data into the database
        try:
            cursor.execute('''
                INSERT INTO videos (title, url, video_length, channel, transcription)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, url, video_length, channel, self.transcription_txt))
            conn.commit()
            print(f"Data inserted into database for video: {title}")
        except Exception as e:
            print(f"Error inserting data into database: {e}")
        finally:
            conn.close()

    # Optional: Define a method to verify the table schema
    def verify_table_schema(self, cursor):
        cursor.execute("PRAGMA table_info('videos');")
        columns = cursor.fetchall()
        # Check if expected columns exist and have correct types
        expected_columns = {
            'id': 'INTEGER',
            'title': 'TEXT',
            'url': 'TEXT',
            'video_length': 'INTEGER',
            'channel': 'TEXT',
            'transcription': 'TEXT'
        }
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            if col_name in expected_columns:
                if col_type.upper() != expected_columns[col_name]:
                    print(f"Column '{col_name}' has type '{col_type}', expected '{expected_columns[col_name]}'.")
            else:
                print(f"Unexpected column '{col_name}' found in 'videos' table.")
        # You can add logic to handle schema mismatches if needed
