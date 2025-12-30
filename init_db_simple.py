#!/usr/bin/env python3
"""
Simple database initialization for YouTube Management System
"""
import sqlite3
import os

def init_simple_db():
    """Initialize database with basic tables"""
    # Ensure database directory exists
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect('database/data.db')
    cursor = conn.cursor()
    
    # YouTubers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS youtubers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            channel_link TEXT,
            niche TEXT,
            contact TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            youtuber_id INTEGER,
            date_uploaded DATE,
            payment_status TEXT DEFAULT 'pending',
            amount DECIMAL(10,2) DEFAULT 0.00,
            video_link TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (youtuber_id) REFERENCES youtubers (id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_youtuber_id ON videos(youtuber_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_payment_status ON videos(payment_status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_date_uploaded ON videos(date_uploaded)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_youtubers_name ON youtubers(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_youtubers_niche ON youtubers(niche)')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_simple_db()
