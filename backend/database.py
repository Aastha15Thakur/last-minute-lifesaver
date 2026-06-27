import sqlite3
import os

DB_FILE = "lifesaver.db"

def get_db_connection():
    """Establishes a connection to the SQLite database file."""
    conn = sqlite3.connect(DB_FILE)
    # This row_factory configuration allows us to access columns by name like dictionary keys
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates tables if they do not exist yet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create the Main Tasks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            deadline TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Create the Subtasks Table (Linked via task_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0, -- 0 for False, 1 for True
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✨ Database initialized successfully with tasks and subtasks tables!")

# Automatically run the initialization when this file is imported or executed
if __name__ == "__main__":
    init_db()