@echo off
echo Starting YouTuber Management System (Production Mode)...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting production server with Gunicorn...
echo Open your browser and go to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 120
pause
