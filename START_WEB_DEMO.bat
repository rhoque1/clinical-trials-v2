@echo off
echo ================================================================================
echo Clinical Trial Matching System - Web Interface
echo ================================================================================
echo.
echo Starting web server...
echo.
echo The web interface will open in your browser at: http://localhost:8501
echo.
echo To stop the server, press Ctrl+C in this window
echo.
echo ================================================================================
echo.

streamlit run app.py

pause
