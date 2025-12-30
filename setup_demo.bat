@echo off
echo Setting up YouTuber Management System with Demo Data...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Creating sample data...
python sample_data.py
echo.
echo Setup complete! You can now run the application.
echo.
echo To start the application, run: python app.py
echo Then open your browser to: http://localhost:5000
echo.
pause
