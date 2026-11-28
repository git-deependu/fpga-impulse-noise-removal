#!/usr/bin/env python3
"""
=============================================================================
process_custom_image.py
-----------------------
Process ANY custom user image (PNG, JPG, BMP) through the FPGA Hardware
Impulse Noise Filter:
  1. Loads any user photo and converts to 8-bit grayscale.
  2. Resizes to 64x64 for hardware line-buffer compatibility.
  3. Injects salt-and-pepper noise at 5%, 10%, 20%, and 30%.
  4. Runs Software Benchmarks: Standard Median (SMF) & Adaptive Median (AMF).
  5. Simulates the synthesizable Verilog RTL via Icarus Verilog (vvp)
     directly on your custom image!
  6. Reads the FPGA DUT output and computes MSE, PSNR, and SSIM.
  7. Saves side-by-side 5-panel visual comparison figures.
  8. Opens the filtered image so you can show it to your professor immediately!
=============================================================================
"""

import os
import sys
import argparse
import subprocess
from PIL import Image
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SW_DIR = os.path.join(PROJECT_ROOT, "software_model")
RESULTS_DIR = os.path.join(SW_DIR, "results")
SIM_OUT = os.path.join(PROJECT_ROOT, "rtl", "sim_out")
sys.path.insert(0, SW_DIR)

from noise_generator import add_salt_and_pepper
from filters import median_filter_3x3, decision_based_median_filter, adaptive_median_filter
from metrics import evaluate, print_metrics
from run_verification import compile_rtl, check_prerequisites, VVP

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def save_raw(array: np.ndarray, path: str) -> None:
    with open(path, "w") as f:
        for val in array.ravel():
            f.write(f"{int(val):02x}\n")


def load_raw(path: str, shape: tuple[int, int]) -> np.ndarray:
    with open(path) as f:
        vals = [int(line.strip(), 16) for line in f if line.strip()]
    return np.array(vals, dtype=np.uint8).reshape(shape)


def save_comparison_figure(original, noisy, smf_out, hw_out, amf_out,
                           density: float, basename: str, out_path: str) -> None:
    if not MATPLOTLIB_AVAILABLE:
        return
    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    titles = [
        "1. Original",
        f"2. Noisy (d={density:.0%})",
        "3. Standard Median (SMF)",
        "4. FPGA Hardware Filter",
        "5. Adaptive Median (AMF)",
    ]
    images = [original, noisy, smf_out, hw_out, amf_out]
    for ax, img, title in zip(axes, images, titles):
        ax.imshow(img, cmap="gray", vmin=0, vmax=255)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.axis("off")

    fig.suptitle(f"Custom Image Demonstration: '{basename}' | Noise Density = {density:.0%}",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def process_image(image_path: str):
    print("=" * 70)
    print("       FPGA Impulse Noise Removal — Custom Image Workflow")
    print("=" * 70)

    if not os.path.isfile(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return False

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(SIM_OUT, exist_ok=True)

    # 1. Load, convert to grayscale, and resize to 64x64
    basename = os.path.splitext(os.path.basename(image_path))[0]
    print(f"\n[1/4] Loading: {os.path.basename(image_path)}")
    img = Image.open(image_path).convert("L")
    if img.size != (64, 64):
        print(f"  [i] Resizing from {img.size} to 64x64 for FPGA line-buffer architecture...")
        resample = getattr(Image.Resampling, "LANCZOS", Image.LANCZOS)
        img = img.resize((64, 64), resample=resample)

    original = np.array(img, dtype=np.uint8)
    orig_png = os.path.join(RESULTS_DIR, f"{basename}_original.png")
    Image.fromarray(original).save(orig_png)
    print(f"  [OK] Input image pre-processed: {orig_png}")

    # 2. Compile Verilog RTL
    print(f"\n[2/4] Compiling Verilog RTL hardware architecture...")
    if not check_prerequisites():
        return False
    sim_exe = compile_rtl()
    if not sim_exe:
        print("[FAIL] RTL compilation failed.")
        return False

    # 3. Process across noise densities
    print(f"\n[3/4] Simulating FPGA RTL & software models on '{basename}'...")
    densities = [0.05, 0.10, 0.20, 0.30]
    rng = np.random.default_rng(42)
    summary_rows = []

    for d in densities:
        tag = f"{int(d*100):02d}pct"
        print(f"\n  --- Processing Noise Density: {d:.0%} ---")

        # Corrupt image
        noisy = add_salt_and_pepper(original, d, rng)
        noisy_raw = os.path.join(RESULTS_DIR, f"{basename}_noisy_{tag}.raw")
        save_raw(noisy, noisy_raw)

        # Software filters
        smf_out = median_filter_3x3(noisy)
        dbmf_out = decision_based_median_filter(noisy)
        amf_out = adaptive_median_filter(noisy, min_window=3, max_window=7)

        # Run Verilog RTL simulation via Icarus Verilog
        dut_raw = os.path.join(SIM_OUT, f"dut_output_{basename}_{tag}.raw")
        sim_cmd = [
            VVP,
            sim_exe,
            f"+INPUT_FILE=../../software_model/results/{basename}_noisy_{tag}.raw",
            f"+EXPECTED_FILE=../../software_model/results/{basename}_noisy_{tag}.raw", # dummy expected for run
            f"+OUTPUT_FILE=../sim_out/dut_output_{basename}_{tag}.raw",
        ]
        res = subprocess.run(sim_cmd, cwd=SIM_OUT, capture_output=True, text=True)

        # Load FPGA hardware simulation output
        hw_out = load_raw(dut_raw, (64, 64))

        # Save images
        Image.fromarray(noisy).save(os.path.join(RESULTS_DIR, f"{basename}_noisy_{tag}.png"))
        Image.fromarray(smf_out).save(os.path.join(RESULTS_DIR, f"{basename}_smf_{tag}.png"))
        Image.fromarray(hw_out).save(os.path.join(RESULTS_DIR, f"{basename}_fpga_rtl_{tag}.png"))
        Image.fromarray(amf_out).save(os.path.join(RESULTS_DIR, f"{basename}_amf_{tag}.png"))

        # Calculate metrics
        noisy_m = evaluate(original, noisy, label="Noisy")
        smf_m   = evaluate(original, smf_out, label="SMF")
        hw_m    = evaluate(original, hw_out, label="FPGA HW-RTL")
        amf_m   = evaluate(original, amf_out, label="AMF")

        print(f"    Noisy Input    : PSNR = {noisy_m['psnr_db']:.2f} dB,  SSIM = {noisy_m['ssim']:.4f}")
        print(f"    Standard Median: PSNR = {smf_m['psnr_db']:.2f} dB,  SSIM = {smf_m['ssim']:.4f}")
        print(f"    FPGA HW Filter : PSNR = {hw_m['psnr_db']:.2f} dB,  SSIM = {hw_m['ssim']:.4f}  "
              f"(Improvement: +{hw_m['psnr_db'] - smf_m['psnr_db']:.2f} dB)")

        # Save 5-panel figure
        fig_path = os.path.join(RESULTS_DIR, f"{basename}_{tag}_comparison.png")
        save_comparison_figure(original, noisy, smf_out, hw_out, amf_out, d, basename, fig_path)

        summary_rows.append({
            "density": f"{d:.0%}",
            "smf_psnr": f"{smf_m['psnr_db']:.2f} dB",
            "hw_psnr": f"{hw_m['psnr_db']:.2f} dB",
            "hw_ssim": f"{hw_m['ssim']:.4f}",
            "gain": f"+{hw_m['psnr_db'] - smf_m['psnr_db']:.2f} dB"
        })

    # 4. Print Summary Table
    print("\n" + "=" * 70)
    print(f"  Final Performance Summary for Custom Image: '{basename}'")
    print("=" * 70)
    print(f"{'Noise Density':<15} {'SMF PSNR':<12} {'FPGA RTL PSNR':<16} {'FPGA SSIM':<12} {'Gain vs SMF':<12}")
    print("-" * 70)
    for r in summary_rows:
        print(f"{r['density']:<15} {r['smf_psnr']:<12} {r['hw_psnr']:<16} {r['hw_ssim']:<12} {r['gain']:<12}")
    print("=" * 70)

    preview_fig = os.path.join(RESULTS_DIR, f"{basename}_10pct_comparison.png")
    print(f"\n[4/4] Demonstration comparison figure saved to:")
    print(f"  file:///{preview_fig.replace('\\', '/')}")

    # Launch default Windows image viewer
    if os.name == "nt" and os.path.isfile(preview_fig):
        try:
            print("  Opening comparison figure in default photo viewer...")
            os.startfile(preview_fig)
        except Exception:
            pass

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a custom image through the FPGA Impulse Noise Filter.")
    parser.add_argument("image", nargs="?", default=None, help="Path to input image (JPG, PNG, BMP).")
    args = parser.parse_args()

    image_path = args.image
    if not image_path:
        print("\nEnter the path to any image on your PC (or drag and drop it here):")
        image_path = input("Image path: ").strip().strip('"').strip("'")

    if not image_path:
        print("No image provided. Exiting.")
        sys.exit(1)

    process_image(image_path)
