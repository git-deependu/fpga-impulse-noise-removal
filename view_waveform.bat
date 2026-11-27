@echo off
cd /d "%~dp0"

echo Opening GTKWave with simulation waveform...
if exist "C:\iverilog\gtkwave\bin\gtkwave.exe" (
    start "" "C:\iverilog\gtkwave\bin\gtkwave.exe" rtl\sim_out\tb_impulse_noise_filter.vcd
) else (
    start "" gtkwave rtl\sim_out\tb_impulse_noise_filter.vcd
)
