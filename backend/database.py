import sqlite3
import os

DB_FILE = "lifesaver.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create the Main Tasks Table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            deadline TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # --- PREREQUISITE UPGRADE: Migration for Phase 3 additions ---
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN priority TEXT")
        cursor.execute("ALTER TABLE tasks ADD COLUMN reason TEXT")
        cursor.execute("ALTER TABLE tasks ADD COLUMN estimated_hours REAL")
        print("📊 Successfully migrated tasks table with new agent columns!")
    except sqlite3.OperationalError:
        # This catches if the columns are already there, so it won't crash
        pass
    
    # 2. Create the Subtasks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✨ Database initialized successfully!")

if __name__ == "__main__":
    init_db()