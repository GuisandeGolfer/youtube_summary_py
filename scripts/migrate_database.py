#!/usr/bin/env python3
"""
Database Migration Script

Adds missing columns (summary, created_at) to existing transcriptions.db
without deleting any existing data.
"""

import sqlite3
import os


def get_existing_columns(cursor, table_name):
    """Get list of existing columns in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def migrate_database(db_path):
    """Add missing columns to videos table"""

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False

    print(f"📊 Migrating database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get existing columns
        existing_columns = get_existing_columns(cursor, 'videos')
        print(f"✓ Found existing columns: {', '.join(existing_columns)}")

        migrations_applied = []

        # Add 'summary' column if it doesn't exist
        if 'summary' not in existing_columns:
            print("➕ Adding 'summary' column...")
            cursor.execute("ALTER TABLE videos ADD COLUMN summary TEXT")
            migrations_applied.append('summary')
            print("  ✓ Summary column added")
        else:
            print("  ⏭️  Summary column already exists")

        # Add 'created_at' column if it doesn't exist
        # Note: SQLite doesn't support CURRENT_TIMESTAMP as default in ALTER TABLE
        # So we add the column and set a default value for existing rows
        if 'created_at' not in existing_columns:
            print("➕ Adding 'created_at' column...")
            cursor.execute("ALTER TABLE videos ADD COLUMN created_at TIMESTAMP")
            # Set a default timestamp for existing rows (use current time)
            cursor.execute("UPDATE videos SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            migrations_applied.append('created_at')
            print("  ✓ Created_at column added and populated for existing rows")
        else:
            print("  ⏭️  Created_at column already exists")

        # Commit changes
        conn.commit()

        # Verify the changes
        new_columns = get_existing_columns(cursor, 'videos')
        print(f"\n✅ Migration complete!")
        print(f"📋 Current columns: {', '.join(new_columns)}")

        if migrations_applied:
            print(f"🔄 Applied migrations: {', '.join(migrations_applied)}")
        else:
            print("ℹ️  No migrations needed - database already up to date")

        # Show row count to confirm data is intact
        cursor.execute("SELECT COUNT(*) FROM videos")
        count = cursor.fetchone()[0]
        print(f"📹 Total videos in database: {count}")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Get database path (now in data/ directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level to project root
    db_path = os.path.join(project_root, "data", "transcriptions.db")

    print("="*50)
    print("  Database Migration Script")
    print("="*50)
    print()

    success = migrate_database(db_path)

    print()
    if success:
        print("✅ Migration successful! You can now process videos with summaries.")
    else:
        print("❌ Migration failed. Please check the error messages above.")
    print("="*50)
