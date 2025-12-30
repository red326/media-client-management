#!/usr/bin/env python3
"""
Professional setup script for YouTube Management System
"""
import os
import sys
import subprocess
import secrets
import shutil
from pathlib import Path

def print_step(step, message):
    """Print formatted step message"""
    print(f"\n{'='*60}")
    print(f"STEP {step}: {message}")
    print('='*60)

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def create_directories():
    """Create necessary directories"""
    directories = ['database', 'logs', 'uploads', 'backups', 'tests']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment():
    """Setup environment file"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        # Copy example and generate secret key
        with open(env_example, 'r') as f:
            content = f.read()
        
        # Generate a secure secret key
        secret_key = secrets.token_urlsafe(32)
        content = content.replace('your-super-secret-key-here-change-this-in-production', secret_key)
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Created .env file with secure secret key")
    else:
        print("ℹ️  .env file already exists")

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing requirements"):
        print("✅ All dependencies installed successfully")
        return True
    else:
        print("❌ Failed to install dependencies")
        return False

def initialize_database():
    """Initialize database with migrations"""
    print("Initializing database...")
    try:
        from database.migrations import init_database
        init_database('database/data.db')
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def run_tests():
    """Run test suite"""
    print("Running test suite...")
    if run_command(f"{sys.executable} -m pytest tests/ -v", "Running tests"):
        print("✅ All tests passed")
        return True
    else:
        print("⚠️  Some tests failed - check output above")
        return False

def create_startup_scripts():
    """Create startup scripts for different environments"""
    
    # Development script
    dev_script = """#!/bin/bash
# Development startup script
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
"""
    
    # Production script
    prod_script = """#!/bin/bash
# Production startup script
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
"""
    
    # Windows batch files
    dev_bat = """@echo off
REM Development startup script for Windows
set FLASK_ENV=development
set FLASK_DEBUG=1
python app.py
pause
"""
    
    prod_bat = """@echo off
REM Production startup script for Windows
set FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
pause
"""
    
    scripts = [
        ('scripts/dev.sh', dev_script),
        ('scripts/prod.sh', prod_script),
        ('scripts/dev.bat', dev_bat),
        ('scripts/prod.bat', prod_bat)
    ]
    
    for script_path, content in scripts:
        Path(script_path).parent.mkdir(exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(content)
        
        # Make shell scripts executable on Unix systems
        if script_path.endswith('.sh') and os.name != 'nt':
            os.chmod(script_path, 0o755)
        
        print(f"✅ Created startup script: {script_path}")

def main():
    """Main setup function"""
    print("🚀 YouTube Management System - Professional Setup")
    print("This script will set up your application for development or production use.")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print_step(1, "Creating Directory Structure")
    create_directories()
    
    print_step(2, "Setting Up Environment Configuration")
    setup_environment()
    
    print_step(3, "Installing Dependencies")
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    print_step(4, "Initializing Database")
    if not initialize_database():
        print("❌ Setup failed at database initialization")
        sys.exit(1)
    
    print_step(5, "Running Tests")
    run_tests()  # Don't fail setup if tests fail
    
    print_step(6, "Creating Startup Scripts")
    create_startup_scripts()
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review and update .env file with your specific settings")
    print("2. For development: python app.py or ./scripts/dev.sh")
    print("3. For production: ./scripts/prod.sh or use Docker")
    print("4. Access your application at http://localhost:5000")
    print("\nFor Docker deployment:")
    print("  docker-compose up -d")
    print("\nFor more information, see README.md")

if __name__ == '__main__':
    main()
