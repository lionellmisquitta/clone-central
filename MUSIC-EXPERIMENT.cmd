@echo off
setlocal
cd /d "%~dp0"
echo ==============================
echo Clone Central - Music test
echo ==============================
where py >nul 2>&1
if errorlevel 1 (
 echo Python launcher not found. Install Python 3.12 from python.org.
 pause
 exit /b 1
)
py -3.12 --version >nul 2>&1
if errorlevel 1 (
 echo Python 3.12 is required for this experiment.
 pause
 exit /b 1
)
if not exist ".venv-music\Scripts\python.exe" (
 echo Creating music Python environment...
 py -3.12 -m venv .venv-music
 if errorlevel 1 goto :failed
)
".venv-music\Scripts\python.exe" -c "import demucs" >nul 2>&1
if errorlevel 1 (
 echo Installing Demucs. Model downloads occur later.
 ".venv-music\Scripts\python.exe" -m pip install demucs
 if errorlevel 1 goto :failed
)
echo.
set /p "SONG=Full path to your authorized input WAV: "
echo Quality modes: fast, balanced, studio
set /p "MODE=Choose mode [fast]: "
if "%MODE%"=="" set "MODE=fast"
".venv-music\Scripts\python.exe" experiments\separate_music.py "%SONG%" --mode "%MODE%" --output-dir "outputs\stems"
if errorlevel 1 goto :failed
echo.
echo Finished. Check outputs\stems for vocals.wav and no_vocals.wav
pause
exit /b 0
:failed
echo.
echo Music experiment failed. Please save the error without sharing private audio.
pause
exit /b 1
