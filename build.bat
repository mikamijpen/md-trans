@echo off
CALL conda activate tools
pyinstaller --onefile --windowed --name md-trans main.py
pause 