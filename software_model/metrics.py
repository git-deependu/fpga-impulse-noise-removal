"""
metrics.py
----------
Image-quality evaluation metrics for the FPGA impulse-noise-removal project.

Implements:
  - MSE  (Mean Squared Error)
  - PSNR (Peak Signal-to-Noise Ratio)
  - SSIM (Structural Similarity Index Measure)  ← full manual implementation,
          no scikit-image dependency required
"""

import math
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# MSE
# ─────────────────────────────────────────────────────────────────────────────

def mse(reference: np.ndarray, test: np.ndarray) -> float:
    """
    Mean Squared Error between *reference* and *test* images.

    Parameters
    ----------
    reference, test : H×W uint8 (or float) numpy arrays of the same shape.

    Returns
    -------
    mse_value : float — lower is better; 0 means identical.
    """
    _check_compatible(reference, test)
    diff = reference.astype(np.float64) - test.astype(np.float64)
    return float(np.mean(diff ** 2))


# ─────────────────────────────────────────────────────────────────────────────
# PSNR
# ─────────────────────────────────────────────────────────────────────────────

def psnr(reference: np.ndarray, test: np.ndarray,
         max_value: float = 255.0) -> float:
    """
    Peak Signal-to-Noise Ratio (dB).

    Parameters
    ----------
    reference, test : H×W uint8 numpy arrays.
    max_value       : Maximum pixel value (255 for 8-bit images).

    Returns
    -------
    psnr_db : float — higher is better; inf if the images are identical.
    """
    mse_val = mse(reference, test)
    if mse_val == 0.0:
        return float("inf")
    return 10.0 * math.log10(max_value ** 2 / mse_val)


# ─────────────────────────────────────────────────────────────────────────────
# SSIM
# ─────────────────────────────────────────────────────────────────────────────

def _gaussian_kernel_1d(size: int, sigma: float) -> np.ndarray:
    """1-D Gaussian kernel, normalised to sum to 1."""
    half = size // 2
    x = np.arange(-half, half + 1, dtype=np.float64)
    kernel = np.exp(-(x ** 2) / (2 * sigma ** 2))
    return kernel / kernel.sum()


def _convolve2d_separable(image: np.ndarray, kernel_1d: np.ndarray) -> np.ndarray:
    """Separable 2-D convolution using a 1-D Gaussian kernel."""
    from scipy.ndimage import convolve1d
    out = convolve1d(image.astype(np.float64), kernel_1d, axis=0, mode="reflect")
    out = convolve1d(out, kernel_1d, axis=1, mode="reflect")
    return out


def ssim(reference: np.ndarray, test: np.ndarray,
         win_size: int = 11, sigma: float = 1.5,
         K1: float = 0.01, K2: float = 0.03,
         max_value: float = 255.0) -> float:
    """
    Structural Similarity Index Measure (SSIM).

    Follows the Wang et al. (2004) definition with a Gaussian window.

    Parameters
    ----------
    reference, test : H×W uint8 numpy arrays.
    win_size        : Gaussian window size (default 11).
    sigma           : Gaussian window standard deviation (default 1.5).
    K1, K2          : Stabilisation constants (default 0.01, 0.03).
    max_value       : Maximum pixel value (default 255.0).

    Returns
    -------
    ssim_value : float in [−1, 1] — 1 means identical.
    """
    _check_compatible(reference, test)

    C1 = (K1 * max_value) ** 2
    C2 = (K2 * max_value) ** 2

    kernel = _gaussian_kernel_1d(win_size, sigma)

    ref_f = reference.astype(np.float64)
    tst_f = test.astype(np.float64)

    mu_ref = _convolve2d_separable(ref_f, kernel)
    mu_tst = _convolve2d_separable(tst_f, kernel)

    mu_ref_sq = mu_ref ** 2
    mu_tst_sq = mu_tst ** 2
    mu_ref_tst = mu_ref * mu_tst

    sigma_ref_sq = _convolve2d_separable(ref_f ** 2, kernel) - mu_ref_sq
    sigma_tst_sq = _convolve2d_separable(tst_f ** 2, kernel) - mu_tst_sq
    sigma_ref_tst = _convolve2d_separable(ref_f * tst_f, kernel) - mu_ref_tst

    # Clamp variances to avoid tiny negatives from floating-point rounding
    sigma_ref_sq = np.maximum(sigma_ref_sq, 0.0)
    sigma_tst_sq = np.maximum(sigma_tst_sq, 0.0)

    numerator   = (2 * mu_ref_tst + C1) * (2 * sigma_ref_tst + C2)
    denominator = (mu_ref_sq + mu_tst_sq + C1) * (sigma_ref_sq + sigma_tst_sq + C2)

    ssim_map = numerator / denominator
    return float(np.mean(ssim_map))


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: compute all metrics at once
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(reference: np.ndarray, test: np.ndarray,
             label: str = "") -> dict:
    """
    Compute MSE, PSNR, and SSIM for a (reference, test) image pair.

    Returns
    -------
    metrics : dict with keys 'label', 'mse', 'psnr_db', 'ssim'.
    """
    return {
        "label"  : label,
        "mse"    : mse(reference, test),
        "psnr_db": psnr(reference, test),
        "ssim"   : ssim(reference, test),
    }


def print_metrics(metrics: dict) -> None:
    """Pretty-print a metrics dictionary."""
    label = metrics.get("label", "")
    hdr = f" {label} " if label else ""
    sep = "-" * 12
    print(f"{sep}{hdr}{sep}")
    print(f"  MSE    = {metrics['mse']:.4f}")
    print(f"  PSNR   = {metrics['psnr_db']:.2f} dB")
    print(f"  SSIM   = {metrics['ssim']:.4f}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _check_compatible(a: np.ndarray, b: np.ndarray) -> None:
    if a.shape != b.shape:
        raise ValueError(
            f"Image shapes must match: got {a.shape} vs {b.shape}."
        )
    if a.ndim != 2:
        raise ValueError("Expected 2-D (H×W) grayscale image arrays.")
