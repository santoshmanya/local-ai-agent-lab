@echo off
REM Moltbook Reader Batch Job
REM Runs the Python script to fetch Moltbook forum posts

cd /d "%~dp0"
python moltbook_reader.py >> "..\data\moltbook\reader.log" 2>&1
