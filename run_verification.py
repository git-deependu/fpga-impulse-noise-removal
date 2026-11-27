#!/usr/bin/env python3
"""
=============================================================================
run_verification.py
-------------------
Automated verification and test runner for the FPGA Impulse Noise Filter project.
Compiles Verilog RTL with Icarus Verilog (iverilog), simulates with vvp across
all test datasets (5%, 10%, 20%, 30% noise), checks 100% bit-exact equivalence,
and summarizes metrics.
=============================================================================
"""

import os
import sys
import subprocess
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RTL_DIR = os.path.join(PROJECT_ROOT, "rtl")
SRC_DIR = os.path.join(RTL_DIR, "src")
TB_DIR = os.path.join(RTL_DIR, "tb")
SIM_OUT = os.path.join(RTL_DIR, "sim_out")
SW_RESULTS = os.path.join(PROJECT_ROOT, "software_model", "results")

# Locate tools
IVERILOG = shutil.which("iverilog") or r"C:\iverilog\bin\iverilog.exe"
VVP = shutil.which("vvp") or r"C:\iverilog\bin\vvp.exe"
GTKWAVE = shutil.which("gtkwave") or r"C:\iverilog\gtkwave\bin\gtkwave.exe"


def check_prerequisites():
    os.makedirs(SIM_OUT, exist_ok=True)
    if not os.path.isfile(IVERILOG):
        print(f"[ERROR] iverilog executable not found at: {IVERILOG}")
        return False
    if not os.path.isfile(VVP):
        print(f"[ERROR] vvp executable not found at: {VVP}")
        return False
    return True


def compile_rtl():
    print("=" * 65)
    print("  [1/3] Compiling Verilog RTL with Icarus Verilog...")
    print("=" * 65)

    sources = [
        os.path.join(SRC_DIR, "line_buffer.v"),
        os.path.join(SRC_DIR, "noise_detector.v"),
        os.path.join(SRC_DIR, "median_filter_3x3.v"),
        os.path.join(SRC_DIR, "window_generator.v"),
        os.path.join(SRC_DIR, "impulse_noise_filter.v"),
        os.path.join(TB_DIR, "tb_impulse_noise_filter.v"),
    ]

    sim_exe = os.path.join(SIM_OUT, "sim_impulse_noise.vvp")

    cmd = [
        IVERILOG,
        "-g2012",
        "-o", sim_exe,
        "-I", SRC_DIR,
    ] + sources

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[FAIL] Compilation failed:\n{res.stderr}")
        return None
    print("  [OK] Compilation successful: sim_out/sim_impulse_noise.vvp")
    return sim_exe


def run_simulations(sim_exe):
    print("\n" + "=" * 65)
    print("  [2/3] Simulating across multiple noise densities...")
    print("=" * 65)

    densities = ["05pct", "10pct", "20pct", "30pct"]
    results = {}

    for d in densities:
        in_file = f"../../software_model/results/synthetic_noisy_{d}.raw"
        exp_file = f"../../software_model/results/synthetic_hw_ref_{d}.raw"
        out_file = f"../sim_out/dut_output_{d}.raw"

        cmd = [
            VVP,
            sim_exe,
            f"+INPUT_FILE={in_file}",
            f"+EXPECTED_FILE={exp_file}",
            f"+OUTPUT_FILE={out_file}",
        ]

        res = subprocess.run(cmd, cwd=SIM_OUT, capture_output=True, text=True)
        passed = "RESULT : PASS  -- 100% BIT-EXACT MATCH!" in res.stdout
        results[d] = {
            "passed": passed,
            "stdout": res.stdout,
        }

        status_str = "[PASS] 100% BIT-EXACT (0 mismatches / 4096 pixels)" if passed else "[FAIL] Mismatches detected"
        print(f"  Noise density {d[:2]}%: {status_str}")

    return results


def print_summary(results):
    print("\n" + "=" * 65)
    print("  [3/3] Verification Summary")
    print("=" * 65)
    all_passed = all(r["passed"] for r in results.values())

    print(f"  Total tests run   : {len(results)}")
    print(f"  Tests passed      : {sum(1 for r in results.values() if r['passed'])}")
    print(f"  Tests failed      : {sum(1 for r in results.values() if not r['passed'])}")
    print(f"  Overall Status    : {'ALL TESTS PASSED [PASS]' if all_passed else 'SOME TESTS FAILED [FAIL]'}")
    print("=" * 65)

    print("\n  Waveform VCD generated at:")
    print(f"    {os.path.join(SIM_OUT, 'tb_impulse_noise_filter.vcd')}")
    print(f"  To view in GTKWave, run:")
    print(f"    gtkwave {os.path.join(SIM_OUT, 'tb_impulse_noise_filter.vcd')}")
    return all_passed


if __name__ == "__main__":
    if not check_prerequisites():
        sys.exit(1)

    sim_exe = compile_rtl()
    if not sim_exe:
        sys.exit(1)

    results = run_simulations(sim_exe)
    all_passed = print_summary(results)
    sys.exit(0 if all_passed else 1)
