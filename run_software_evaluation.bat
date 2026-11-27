@echo off
cd /d "%~dp0\software_model"
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

echo =================================================================
echo   Running Software Evaluation Benchmarks (SMF, DBMF, AMF, HW)
echo =================================================================

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" evaluate.py
) else (
    python evaluate.py
)

echo.
pause
