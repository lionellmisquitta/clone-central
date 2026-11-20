@echo off
setlocal
cd /d "%~dp0"
echo Clone Central - Model Library
echo.
where py >nul 2>&1
if errorlevel 1 (
 echo Python launcher not found. Install Python 3.12 first.
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
 echo Setting up a small Python environment...
 py -3.12 -m venv .venv
 if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -c "import huggingface_hub, sounddevice, numpy" >nul 2>&1
if errorlevel 1 (
 echo Installing model download support...
 ".venv\Scripts\python.exe" -m pip install huggingface_hub sounddevice numpy
 if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" model_library.py
if errorlevel 1 goto :failed
exit /b 0
:failed
echo.
echo Model Library could not start. Copy any error text for review.
pause
exit /b 1
