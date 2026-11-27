"""
noise_generator.py
------------------
Generates salt-and-pepper (impulse) noise on grayscale images and saves
both the original and the noisy versions for use as software reference
and RTL testbench inputs.

Usage
-----
    python noise_generator.py                  # uses built-in synthetic image
    python noise_generator.py --image path.png # uses a custom image
"""

import argparse
import os
import numpy as np
from PIL import Image


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def add_salt_and_pepper(image: np.ndarray, noise_density: float,
                        rng: np.random.Generator | None = None) -> np.ndarray:
    """
    Add salt-and-pepper noise to an 8-bit grayscale image.

    Parameters
    ----------
    image        : H×W uint8 numpy array (grayscale, values 0-255).
    noise_density: Fraction of pixels to corrupt, in [0, 1].
    rng          : Optional numpy random Generator for reproducibility.

    Returns
    -------
    noisy        : H×W uint8 numpy array with noise applied.
    """
    if image.ndim != 2:
        raise ValueError("Expected a 2-D (H×W) grayscale image array.")
    if not 0.0 <= noise_density <= 1.0:
        raise ValueError("noise_density must be in [0, 1].")

    rng = rng or np.random.default_rng()
    noisy = image.copy()

    # Draw which pixels are corrupted
    mask = rng.random(image.shape)
    salt_threshold = noise_density / 2.0
    pepper_threshold = noise_density - salt_threshold

    noisy[mask < salt_threshold] = 255          # Salt  (white)
    noisy[(mask >= salt_threshold) &
          (mask < salt_threshold + pepper_threshold)] = 0  # Pepper (black)

    return noisy


def make_synthetic_image(height: int = 64, width: int = 64) -> np.ndarray:
    """
    Create a simple synthetic grayscale test image with geometric patterns.
    Useful when no external image is available.
    """
    img = np.zeros((height, width), dtype=np.uint8)

    # Gradient ramp along rows
    for r in range(height):
        img[r, :] = int(r / (height - 1) * 200)

    # Bright rectangle in the centre
    r0, r1 = height // 4, 3 * height // 4
    c0, c1 = width // 4, 3 * width // 4
    img[r0:r1, c0:c1] = 128

    # Dark border stripe
    img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = 20

    return img


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate salt-and-pepper noisy images for the "
                    "FPGA impulse-noise-removal project."
    )
    parser.add_argument("--image", type=str, default=None,
                        help="Path to an input grayscale PNG/JPEG. "
                             "If omitted, a synthetic image is used.")
    parser.add_argument("--densities", type=float, nargs="+",
                        default=[0.05, 0.10, 0.20, 0.30],
                        help="Noise densities to generate (default: 0.05 0.10 0.20 0.30).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42).")
    parser.add_argument("--outdir", type=str, default="images",
                        help="Output directory (default: images/).")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    # ── Load or create source image ──────────────────────────────────────────
    if args.image:
        src = Image.open(args.image).convert("L")
        original = np.array(src, dtype=np.uint8)
        basename = os.path.splitext(os.path.basename(args.image))[0]
    else:
        original = make_synthetic_image(64, 64)
        basename = "synthetic"

    orig_path = os.path.join(args.outdir, f"{basename}_original.png")
    Image.fromarray(original).save(orig_path)
    print(f"[+] Original image saved : {orig_path}  "
          f"(shape={original.shape}, dtype={original.dtype})")

    # ── Add noise at each requested density ─────────────────────────────────
    for density in args.densities:
        noisy = add_salt_and_pepper(original, density, rng)
        tag = f"{int(density * 100):02d}pct"
        noisy_path = os.path.join(args.outdir, f"{basename}_noisy_{tag}.png")
        Image.fromarray(noisy).save(noisy_path)

        corrupted = int(np.sum(noisy != original))
        total = original.size
        print(f"    density={density:.2f}  corrupted={corrupted}/{total} "
              f"({100*corrupted/total:.1f}%)  → {noisy_path}")

    print("\n[✓] Noise generation complete.")


if __name__ == "__main__":
    main()
