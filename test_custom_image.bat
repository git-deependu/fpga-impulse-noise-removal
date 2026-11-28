@echo off
cd /d "%~dp0"
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

echo =================================================================
echo   FPGA Impulse Noise Filter — Custom Image Processor
echo =================================================================

if "%~1"=="" (
    echo.
    echo Drag and drop an image file (PNG/JPG/BMP) onto this script, OR
    set /p "USER_IMG=Enter image path: "
) else (
    set "USER_IMG=%~1"
)

if "%USER_IMG%"=="" (
    echo No image specified.
    pause
    exit /b
)

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" process_custom_image.py "%USER_IMG%"
) else (
    python process_custom_image.py "%USER_IMG%"
)

echo.
pause
