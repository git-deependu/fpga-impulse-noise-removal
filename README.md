# FPGA-Based Architecture for Efficient Impulse Noise Removal in Digital Images

---

## Quick Start

### 1. Run All RTL Simulations & Verification Suite
```powershell
python run_verification.py
```
This script compiles the synthesizable Verilog RTL using Icarus Verilog (`iverilog`), simulates the testbench with `vvp` across all noise densities (5%, 10%, 20%, 30%), and verifies 100% bit-exact equivalence with the software reference model.

### 2. View Waveforms in GTKWave
```powershell
C:\iverilog\gtkwave\bin\gtkwave.exe rtl\sim_out\tb_impulse_noise_filter.vcd
```

### 3. Re-run Software Model Benchmarks
```powershell
cd software_model
python evaluate.py
```
Generates noisy, filtered PNGs, metrics CSV (`results/quality_metrics.csv`), and 5-panel visual comparison figures.

---

## Results Summary

| Metric | Noisy (10%) | Standard Median (SMF) | FPGA HW-RTL Filter | Improvement vs SMF |
|---|---|---|---|---|
| **PSNR** | 15.11 dB | 20.12 dB | **41.10 dB** | **+20.98 dB** |
| **SSIM** | 0.2204 | 0.8285 | **0.9926** | **+0.1641** |
| **MSE** | 2004.86 | 633.06 | **5.05** | **-628.01** |
| **Throughput** | — | — | **1 pixel / clock cycle** | Real-time 1080p @ 60 FPS capable |
| **Bit-Exact Equivalence** | — | — | **100.0% (0 / 4096 mismatches)** | Verified across 5%, 10%, 20%, 30% |

---

## Architecture

- `rtl/src/line_buffer.v`: Parameterized shift-register buffer for $1\times W$ pixel delay.
- `rtl/src/window_generator.v`: Streaming $3\times 3$ sliding window generator.
- `rtl/src/noise_detector.v`: Combinational impulse detector ($0\times 00$ or $0\times \text{FF}$).
- `rtl/src/median_filter_3x3.v`: 5-stage pipelined 25 Compare-and-Swap (CAS) sorting network.
- `rtl/src/impulse_noise_filter.v`: Top-level streaming filter module.
- `rtl/tb/tb_impulse_noise_filter.v`: Self-checking testbench.
- `rtl/synth/synth.tcl`: Vivado batch synthesis script.
