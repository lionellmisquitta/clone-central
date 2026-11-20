@echo off
setlocal
cd /d "%~dp0"
echo ==============================
echo Clone Central - Voice test
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
if not exist ".venv\Scripts\python.exe" (
 echo Creating an isolated Python environment...
 py -3.12 -m venv .venv
 if errorlevel 1 goto :failed
)
echo Checking voice dependencies...
".venv\Scripts\python.exe" -c "import qwen_tts, soundfile" >nul 2>&1
if errorlevel 1 (
 echo Installing Qwen3-TTS and soundfile. Model downloads occur later.
 ".venv\Scripts\python.exe" -m pip install qwen-tts soundfile
 if errorlevel 1 goto :failed
)
echo.
if defined CLONE_CENTRAL_REFERENCE_WAV (
 set "REF=%CLONE_CENTRAL_REFERENCE_WAV%"
 echo Using WAV recorded in Clone Central: %REF%
) else (
 set /p "REF=Full path to your reference voice WAV: "
)
set /p "REF_TEXT=Exact words spoken in that clip: "
set /p "SPEECH=New text to generate: "
echo.
echo Quality modes: fast, balanced, studio
set /p "MODE=Choose mode [fast]: "
if "%MODE%"=="" set "MODE=fast"
echo.
".venv\Scripts\python.exe" experiments\voice_clone.py --reference "%REF%" --reference-text "%REF_TEXT%" --text "%SPEECH%" --mode "%MODE%" --output "outputs\voice.wav"
if errorlevel 1 goto :failed
echo.
echo Finished. See outputs\voice.wav
pause
exit /b 0
:failed
echo.
echo Voice experiment failed. Please save the visible error (without private recordings) for review.
pause
exit /b 1
