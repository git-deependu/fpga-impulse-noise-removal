@echo off
cd /d "%~dp0"
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

echo =================================================================
echo   Running FPGA Impulse Noise Filter Verification Suite
echo =================================================================

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" run_verification.py
) else (
    python run_verification.py
)

echo.
pause
