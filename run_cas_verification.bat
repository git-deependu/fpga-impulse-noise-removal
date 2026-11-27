@echo off
cd /d "%~dp0\software_model"
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

echo =================================================================
echo   Running 25-CAS Sorting Network Mathematical Verification
echo =================================================================

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" verify_cas_network.py
) else (
    python verify_cas_network.py
)

echo.
pause
