@echo off
cd /d "%~dp0"

echo Opening GTKWave with pre-configured waveform signals...
set "GTK_EXE=C:\iverilog\gtkwave\bin\gtkwave.exe"
set "VCD_FILE=rtl\sim_out\tb_impulse_noise_filter.vcd"
set "GTKW_FILE=rtl\sim_out\tb_impulse_noise_filter.gtkw"

if exist "%GTK_EXE%" (
    start "" "%GTK_EXE%" "%VCD_FILE%" "%GTKW_FILE%"
) else (
    start "" gtkwave "%VCD_FILE%" "%GTKW_FILE%"
)
