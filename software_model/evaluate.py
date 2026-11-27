"""
evaluate.py
-----------
Main evaluation script for the software reference model and FPGA hardware model.

For each test image and each noise density:
  1. Adds salt-and-pepper noise.
  2. Applies:
     - SMF  (Standard 3×3 Median Filter)
     - DBMF (Decision-Based 3×3 Median Filter - Synopsis reference)
     - HW   (Cycle-accurate RTL streaming model)
     - AMF  (Adaptive Median Filter)
  3. Computes MSE, PSNR, and SSIM.
  4. Saves filtered images and raw hex files for RTL testbench validation.
  5. Exports a CSV summary and comparison figures.
"""

import argparse
import csv
import os
import sys
import numpy as np
from PIL import Image

# ── local modules ─────────────────────────────────────────────────────────────
from noise_generator import add_salt_and_pepper, make_synthetic_image
from filters import (
    median_filter_3x3,
    decision_based_median_filter,
    hardware_streaming_filter,
    adaptive_median_filter
)
from metrics import evaluate, print_metrics

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def load_or_create_image(path: str | None) -> tuple[np.ndarray, str]:
    if path:
        img = Image.open(path).convert("L")
        return np.array(img, dtype=np.uint8), os.path.splitext(os.path.basename(path))[0]
    return make_synthetic_image(64, 64), "synthetic"


def save_png(array: np.ndarray, path: str) -> None:
    Image.fromarray(array).save(path)


def save_raw(array: np.ndarray, path: str) -> None:
    with open(path, "w") as f:
        for val in array.ravel():
            f.write(f"{int(val):02x}\n")


def save_comparison_figure(original, noisy, smf_out, dbmf_out, amf_out,
                            density: float, basename: str, outdir: str) -> None:
    if not MATPLOTLIB_AVAILABLE:
        return

    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    titles = [
        "Original",
        f"Noisy (d={density:.0%})",
        "SMF (Standard 3×3)",
        "DBMF / FPGA Arch",
        "AMF (Adaptive 3×3-7×7)",
    ]
    images = [original, noisy, smf_out, dbmf_out, amf_out]
    for ax, img, title in zip(axes, images, titles):
        ax.imshow(img, cmap="gray", vmin=0, vmax=255)
        ax.set_title(title, fontsize=9)
        ax.axis("off")

    fig.suptitle(f"{basename}  |  noise density = {density:.0%}", fontsize=11, fontweight="bold")
    plt.tight_layout()
    tag = f"{int(density * 100):02d}pct"
    fig_path = os.path.join(outdir, f"{basename}_{tag}_comparison.png")
    plt.savefig(fig_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def run_evaluation(original: np.ndarray, basename: str,
                   densities: list[float], outdir: str,
                   seed: int = 42) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []

    for density in densities:
        tag = f"{int(density * 100):02d}pct"
        print(f"\n{'='*60}")
        print(f"  Image: {basename}   Noise density: {density:.0%}")
        print(f"{'='*60}")

        noisy = add_salt_and_pepper(original, density, rng)
        smf_out = median_filter_3x3(noisy)
        dbmf_out = decision_based_median_filter(noisy)
        hw_out = hardware_streaming_filter(noisy)
        amf_out = adaptive_median_filter(noisy, min_window=3, max_window=7)

        # Save images
        save_png(noisy, os.path.join(outdir, f"{basename}_noisy_{tag}.png"))
        save_png(smf_out, os.path.join(outdir, f"{basename}_smf_{tag}.png"))
        save_png(dbmf_out, os.path.join(outdir, f"{basename}_dbmf_{tag}.png"))
        save_png(hw_out, os.path.join(outdir, f"{basename}_hw_{tag}.png"))
        save_png(amf_out, os.path.join(outdir, f"{basename}_amf_{tag}.png"))

        # Save raw hex for RTL verification
        save_raw(noisy, os.path.join(outdir, f"{basename}_noisy_{tag}.raw"))
        save_raw(hw_out, os.path.join(outdir, f"{basename}_hw_ref_{tag}.raw"))
        save_raw(dbmf_out, os.path.join(outdir, f"{basename}_dbmf_{tag}.raw"))

        # Metrics
        noisy_metrics = evaluate(original, noisy, label="Noisy vs Original")
        smf_metrics   = evaluate(original, smf_out, label="SMF   vs Original")
        dbmf_metrics  = evaluate(original, dbmf_out, label="DBMF  vs Original")
        hw_metrics    = evaluate(original, hw_out, label="HW-RTL vs Original")
        amf_metrics   = evaluate(original, amf_out, label="AMF   vs Original")

        for m in [noisy_metrics, smf_metrics, dbmf_metrics, hw_metrics, amf_metrics]:
            print_metrics(m)

        save_comparison_figure(original, noisy, smf_out, dbmf_out, amf_out,
                               density, basename, outdir)

        for m, kind in [(noisy_metrics, "noisy"),
                        (smf_metrics, "smf"),
                        (dbmf_metrics, "dbmf"),
                        (hw_metrics, "hw_rtl"),
                        (amf_metrics, "amf")]:
            rows.append({
                "image": basename,
                "density": density,
                "kind": kind,
                "mse": round(m["mse"], 4),
                "psnr_db": round(m["psnr_db"], 2),
                "ssim": round(m["ssim"], 4),
            })

    return rows


def main():
    parser = argparse.ArgumentParser(description="Evaluate Impulse Noise Removal Software Models.")
    parser.add_argument("--image", type=str, default=None)
    parser.add_argument("--densities", type=float, nargs="+", default=[0.05, 0.10, 0.20, 0.30])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", type=str, default="results")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    original, basename = load_or_create_image(args.image)
    save_png(original, os.path.join(args.outdir, f"{basename}_original.png"))
    save_raw(original, os.path.join(args.outdir, f"{basename}_original.raw"))

    rows = run_evaluation(original, basename, args.densities, args.outdir, args.seed)

    csv_path = os.path.join(args.outdir, "quality_metrics.csv")
    fieldnames = ["image", "density", "kind", "mse", "psnr_db", "ssim"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[OK] Metrics CSV saved : {csv_path}")

    sep = "-" * 70
    print(f"\n{sep}")
    print(f"{'Image':<14} {'Density':>7}  {'Kind':<7}  "
          f"{'MSE':>9}  {'PSNR (dB)':>10}  {'SSIM':>7}")
    print(f"{sep}")
    for r in rows:
        print(f"{r['image']:<14} {r['density']:>7.0%}  {r['kind']:<7}  "
              f"{r['mse']:>9.2f}  {r['psnr_db']:>10.2f}  {r['ssim']:>7.4f}")
    print(f"{sep}")
    print("\n[OK] Evaluation complete.")


if __name__ == "__main__":
    main()
