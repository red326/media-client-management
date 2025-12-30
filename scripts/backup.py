#!/usr/bin/env python3
"""
Backup script for YouTube Management System
"""
import os
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
import argparse

def create_backup(backup_type='full', output_dir='backups'):
    """Create backup of the application"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"youtube_mgmt_backup_{backup_type}_{timestamp}"
    
    # Create backup directory
    backup_dir = Path(output_dir)
    backup_dir.mkdir(exist_ok=True)
    
    if backup_type == 'database':
        # Database only backup
        backup_file = backup_dir / f"{backup_name}.db"
        if Path('database/data.db').exists():
            shutil.copy2('database/data.db', backup_file)
            print(f"✅ Database backup created: {backup_file}")
        else:
            print("❌ Database file not found")
            return None
    
    elif backup_type == 'full':
        # Full application backup
        backup_file = backup_dir / f"{backup_name}.zip"
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add database
            if Path('database/data.db').exists():
                zipf.write('database/data.db', 'database/data.db')
            
            # Add configuration files
            for config_file in ['.env', 'config.py', 'requirements.txt']:
                if Path(config_file).exists():
                    zipf.write(config_file, config_file)
            
            # Add logs (last 7 days only)
            if Path('logs').exists():
                for log_file in Path('logs').glob('*.log'):
                    if (datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)).days <= 7:
                        zipf.write(log_file, f"logs/{log_file.name}")
            
            # Add uploads if they exist
            if Path('uploads').exists():
                for upload_file in Path('uploads').rglob('*'):
                    if upload_file.is_file():
                        zipf.write(upload_file, f"uploads/{upload_file.relative_to('uploads')}")
        
        print(f"✅ Full backup created: {backup_file}")
    
    return backup_file

def restore_backup(backup_file, restore_type='database'):
    """Restore from backup"""
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    # Create backup of current state before restore
    print("Creating backup of current state...")
    current_backup = create_backup('full', 'backups/pre_restore')
    
    try:
        if restore_type == 'database' and backup_path.suffix == '.db':
            # Restore database only
            if Path('database/data.db').exists():
                shutil.copy2('database/data.db', 'database/data.db.backup')
            
            shutil.copy2(backup_file, 'database/data.db')
            print(f"✅ Database restored from: {backup_file}")
        
        elif restore_type == 'full' and backup_path.suffix == '.zip':
            # Restore full backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall('.')
            print(f"✅ Full restore completed from: {backup_file}")
        
        else:
            print(f"❌ Invalid backup file type for restore type: {restore_type}")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        if current_backup:
            print(f"Current state backed up to: {current_backup}")
        return False

def cleanup_old_backups(backup_dir='backups', keep_days=30):
    """Clean up old backup files"""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        return
    
    cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    deleted_count = 0
    
    for backup_file in backup_path.glob('youtube_mgmt_backup_*'):
        if backup_file.stat().st_mtime < cutoff_date:
            backup_file.unlink()
            deleted_count += 1
            print(f"🗑️  Deleted old backup: {backup_file.name}")
    
    print(f"✅ Cleaned up {deleted_count} old backup files")

def verify_database():
    """Verify database integrity"""
    db_path = 'database/data.db'
    if not Path(db_path).exists():
        print("❌ Database file not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check database integrity
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()[0]
        
        if result == 'ok':
            print("✅ Database integrity check passed")
            
            # Get table counts
            cursor.execute('SELECT COUNT(*) FROM youtubers')
            youtuber_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM videos')
            video_count = cursor.fetchone()[0]
            
            print(f"📊 Database contains: {youtuber_count} YouTubers, {video_count} videos")
            
            conn.close()
            return True
        else:
            print(f"❌ Database integrity check failed: {result}")
            conn.close()
            return False
    
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='YouTube Management System Backup Tool')
    parser.add_argument('action', choices=['backup', 'restore', 'cleanup', 'verify'],
                       help='Action to perform')
    parser.add_argument('--type', choices=['database', 'full'], default='full',
                       help='Backup type (default: full)')
    parser.add_argument('--file', help='Backup file path for restore')
    parser.add_argument('--output-dir', default='backups',
                       help='Output directory for backups (default: backups)')
    parser.add_argument('--keep-days', type=int, default=30,
                       help='Days to keep backups during cleanup (default: 30)')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        backup_file = create_backup(args.type, args.output_dir)
        if backup_file:
            print(f"\n🎉 Backup completed successfully!")
            print(f"Backup file: {backup_file}")
    
    elif args.action == 'restore':
        if not args.file:
            print("❌ --file argument required for restore")
            return
        
        if restore_backup(args.file, args.type):
            print(f"\n🎉 Restore completed successfully!")
        else:
            print(f"\n❌ Restore failed!")
    
    elif args.action == 'cleanup':
        cleanup_old_backups(args.output_dir, args.keep_days)
        print(f"\n🎉 Cleanup completed!")
    
    elif args.action == 'verify':
        if verify_database():
            print(f"\n🎉 Database verification passed!")
        else:
            print(f"\n❌ Database verification failed!")

if __name__ == '__main__':
    main()
