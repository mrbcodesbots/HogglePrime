@echo off
REM HogglePrime Folder Structure Setup
REM Run this script from: C:\Users\jason\Documents\HogglePrime

echo Creating HogglePrime folder structure...

REM Main directories
mkdir prompts 2>nul
mkdir memories 2>nul
mkdir memories\daily 2>nul
mkdir memories\people 2>nul
mkdir memories\feedback 2>nul
mkdir knowledge 2>nul
mkdir knowledge\multimedia-heroes 2>nul
mkdir knowledge\construct3 2>nul
mkdir knowledge\classroom 2>nul
mkdir n8n-workflows 2>nul
mkdir scripts 2>nul
mkdir config 2>nul
mkdir config\ollama-modelfiles 2>nul
mkdir webapp 2>nul
mkdir webapp\teacher-dashboard 2>nul
mkdir webapp\public-display 2>nul
mkdir webapp\siteground-terminal 2>nul
mkdir logs 2>nul

echo.
echo Folder structure created!
echo.
echo Next steps:
echo 1. Copy MASTERPLAN-HOGGLE.md and CLAUDE.md to this folder
echo 2. Run: git init
echo 3. Run: git add .
echo 4. Run: git commit -m "Initial HogglePrime setup"
echo.
pause
