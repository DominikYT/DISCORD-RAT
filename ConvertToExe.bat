@echo off

pip install pyinstaller
cls
set /p name=Enter Name of Discord Rat File (with .py): 
python -m PyInstaller --onefile --noconsole --uac-admin %name%
echo Converted to exe! Delete folder build. Check folder dist.
pause
