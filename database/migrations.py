"""
Database migration system for YouTube Management System
"""
import sqlite3
import os
from datetime import datetime

class DatabaseMigration:
    """Handle database migrations"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.migrations_table = 'schema_migrations'
    
    def init_migrations_table(self):
        """Initialize migrations tracking table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_applied_migrations(self):
        """Get list of applied migrations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'SELECT version FROM {self.migrations_table}')
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()
    
    def apply_migration(self, version, description, sql_commands):
        """Apply a migration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Execute migration commands
            for command in sql_commands:
                cursor.execute(command)
            
            # Record migration
            cursor.execute(f'''
                INSERT INTO {self.migrations_table} (version, description)
                VALUES (?, ?)
            ''', (version, description))
            
            conn.commit()
            print(f"Applied migration {version}: {description}")
            
        except Exception as e:
            conn.rollback()
            print(f"Failed to apply migration {version}: {e}")
            raise
        finally:
            conn.close()
    
    def run_migrations(self):
        """Run all pending migrations"""
        self.init_migrations_table()
        applied = self.get_applied_migrations()
        
        migrations = [
            {
                'version': '001_initial_schema',
                'description': 'Create initial tables',
                'commands': [
                    '''CREATE TABLE IF NOT EXISTS youtubers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        channel_link TEXT,
                        niche TEXT,
                        contact TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''',
                    '''CREATE TABLE IF NOT EXISTS videos (
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
                    )'''
                ]
            },
            {
                'version': '002_add_indexes',
                'description': 'Add database indexes for performance',
                'commands': [
                    'CREATE INDEX IF NOT EXISTS idx_videos_youtuber_id ON videos(youtuber_id)',
                    'CREATE INDEX IF NOT EXISTS idx_videos_payment_status ON videos(payment_status)',
                    'CREATE INDEX IF NOT EXISTS idx_videos_date_uploaded ON videos(date_uploaded)',
                    'CREATE INDEX IF NOT EXISTS idx_youtubers_name ON youtubers(name)',
                    'CREATE INDEX IF NOT EXISTS idx_youtubers_niche ON youtubers(niche)'
                ]
            },
            {
                'version': '003_add_updated_at_triggers',
                'description': 'Add triggers to update updated_at timestamps',
                'commands': [
                    '''CREATE TRIGGER IF NOT EXISTS update_youtubers_updated_at 
                       AFTER UPDATE ON youtubers
                       BEGIN
                           UPDATE youtubers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                       END''',
                    '''CREATE TRIGGER IF NOT EXISTS update_videos_updated_at 
                       AFTER UPDATE ON videos
                       BEGIN
                           UPDATE videos SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                       END'''
                ]
            },
            {
                'version': '004_add_constraints',
                'description': 'Add data validation constraints',
                'commands': [
                    '''CREATE TABLE IF NOT EXISTS youtubers_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL CHECK(length(name) > 0 AND length(name) <= 100),
                        channel_link TEXT CHECK(channel_link IS NULL OR length(channel_link) <= 500),
                        niche TEXT CHECK(niche IS NULL OR length(niche) <= 50),
                        contact TEXT CHECK(contact IS NULL OR length(contact) <= 100),
                        notes TEXT CHECK(notes IS NULL OR length(notes) <= 1000),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''',
                    '''INSERT INTO youtubers_new SELECT * FROM youtubers''',
                    '''DROP TABLE youtubers''',
                    '''ALTER TABLE youtubers_new RENAME TO youtubers''',
                    
                    '''CREATE TABLE IF NOT EXISTS videos_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL CHECK(length(title) > 0 AND length(title) <= 200),
                        youtuber_id INTEGER NOT NULL,
                        date_uploaded DATE,
                        payment_status TEXT DEFAULT 'pending' CHECK(payment_status IN ('pending', 'paid', 'cancelled')),
                        amount DECIMAL(10,2) DEFAULT 0.00 CHECK(amount >= 0 AND amount <= 999999.99),
                        video_link TEXT CHECK(video_link IS NULL OR length(video_link) <= 500),
                        description TEXT CHECK(description IS NULL OR length(description) <= 1000),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (youtuber_id) REFERENCES youtubers (id) ON DELETE CASCADE
                    )''',
                    '''INSERT INTO videos_new SELECT * FROM videos''',
                    '''DROP TABLE videos''',
                    '''ALTER TABLE videos_new RENAME TO videos'''
                ]
            }
        ]
        
        for migration in migrations:
            if migration['version'] not in applied:
                self.apply_migration(
                    migration['version'],
                    migration['description'],
                    migration['commands']
                )

def init_database(db_path):
    """Initialize database with migrations"""
    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Run migrations
    migration_manager = DatabaseMigration(db_path)
    migration_manager.run_migrations()
    
    print("Database initialized successfully!")

if __name__ == '__main__':
    # Run migrations directly
    db_path = '../database/data.db'
    init_database(db_path)
