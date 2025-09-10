@echo off
echo =====================================
echo   Humanizer Uninstall Script
echo =====================================

REM Stop if not inside the right folder
if not exist ".venv" (
    echo No virtual environment found.
) else (
    echo Removing virtual environment...
    rmdir /s /q .venv
)

REM Remove PyInstaller build files
if exist "build" (
    echo Removing build folder...
    rmdir /s /q build
)

if exist "dist" (
    echo Removing dist folder (EXE output)...
    rmdir /s /q dist
)

if exist "Humanizer.spec" (
    echo Removing PyInstaller spec file...
    del /q Humanizer.spec
)

echo Done. Humanizer has been uninstalled.
pause

