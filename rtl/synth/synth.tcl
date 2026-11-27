# =============================================================================
# synth.tcl — Vivado Batch Synthesis Script
# =============================================================================
# Usage:
#   vivado -mode batch -source synth.tcl
# Target Device: Xilinx Artix-7 (xc7a35tcsg324-1)
# =============================================================================

set target_part "xc7a35tcsg324-1"
set top_module  "impulse_noise_filter"
set output_dir  "./reports"

file mkdir $output_dir

# 1. Read RTL sources
read_verilog -sv ../src/line_buffer.v
read_verilog -sv ../src/noise_detector.v
read_verilog -sv ../src/median_filter_3x3.v
read_verilog -sv ../src/window_generator.v
read_verilog -sv ../src/impulse_noise_filter.v

# 2. Synthesize Design (Out-Of-Context mode for IP/core evaluation)
synth_design -top $top_module -part $target_part -mode out_of_context

# 3. Create timing constraint (100 MHz target, 10.0 ns clock period)
create_clock -name clk -period 10.000 [get_ports clk]

# 4. Generate Reports
report_utilization       -file "$output_dir/utilization_synth.rpt" -pb "$output_dir/utilization_synth.pb"
report_timing_summary    -file "$output_dir/timing_synth.rpt"
report_power             -file "$output_dir/power_synth.rpt"

puts "====================================================================="
puts " Synthesis Complete!"
puts " Reports written to $output_dir/"
puts "====================================================================="
