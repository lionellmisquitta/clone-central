@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
 echo Python launcher missing. Install Python 3.12.
 exit /b 1
)
py -3.12 --version >nul 2>&1
if errorlevel 1 (
 echo Python 3.12 is required.
 exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
 py -3.12 -m venv .venv
 if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" -c "import huggingface_hub, sounddevice" >nul 2>&1
if errorlevel 1 (
 ".venv\Scripts\python.exe" -m pip install huggingface_hub sounddevice
 if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" model_library.py %*
exit /b %errorlevel%
