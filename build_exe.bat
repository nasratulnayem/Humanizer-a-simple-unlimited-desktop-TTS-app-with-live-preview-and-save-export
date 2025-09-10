@echo off
".venv\Scripts\pip.exe" install --upgrade pyinstaller
".venv\Scripts\pyinstaller.exe" --noconfirm --onefile --noconsole --name Humanizer main.py
echo EXE built in dist\Humanizer.exe
