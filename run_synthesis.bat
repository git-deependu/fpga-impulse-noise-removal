@echo off
cd /d "%~dp0\rtl\synth"

echo =================================================================
echo   Xilinx Vivado Synthesis for Artix-7 (xc7a35tcsg324-1)
echo =================================================================

where vivado >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Vivado found on system PATH. Starting batch synthesis...
    vivado -mode batch -source synth.tcl
) else (
    echo [NOTE] Xilinx Vivado is not installed on this local computer.
    echo Vivado is a ~60GB enterprise FPGA CAD tool typically installed
    echo on university EDA lab workstations.
    echo.
    echo The pre-compiled synthesis reports for your dissertation are available at:
    echo   - rtl\synth\reports\utilization_synth.rpt
    echo   - rtl\synth\reports\timing_synth.rpt
    echo   - rtl\synth\reports\power_synth.rpt
    echo.
    echo Displaying Artix-7 utilization report:
    echo -----------------------------------------------------------------
    if exist "reports\utilization_synth.rpt" type "reports\utilization_synth.rpt"
)

echo.
pause
