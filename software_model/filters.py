"""
filters.py
----------
Software reference model for impulse-noise removal.

Implements:
  1. Standard Median Filter (3×3) - SMF
  2. Decision-Based Median Filter (3×3) - DBMF (Synopsis reference)
  3. Hardware-exact streaming model (cycle-accurate matching impulse_noise_filter.v)
  4. Adaptive Median Filter (AMF)
"""

import numpy as np


def _pad_reflect(image: np.ndarray, pad: int) -> np.ndarray:
    return np.pad(image, pad, mode="reflect")


def median_filter_3x3(image: np.ndarray) -> np.ndarray:
    """Standard 3×3 median filter with reflect padding."""
    if image.ndim != 2:
        raise ValueError("Expected a 2-D grayscale image array.")
    padded = _pad_reflect(image, 1)
    H, W = image.shape
    filtered = np.empty_like(image)
    for r in range(H):
        for c in range(W):
            window = padded[r:r+3, c:c+3].ravel()
            filtered[r, c] = int(np.median(window))
    return filtered


def decision_based_median_filter(image: np.ndarray) -> np.ndarray:
    """Decision-Based Median Filter with reflect padding."""
    if image.ndim != 2:
        raise ValueError("Expected a 2-D grayscale image array.")
    padded = _pad_reflect(image, 1)
    H, W = image.shape
    filtered = np.empty_like(image)
    for r in range(H):
        for c in range(W):
            centre = int(image[r, c])
            if centre == 0 or centre == 255:
                window = padded[r:r+3, c:c+3].ravel()
                filtered[r, c] = int(np.median(window))
            else:
                filtered[r, c] = centre
    return filtered


def hardware_streaming_filter(image: np.ndarray) -> np.ndarray:
    """
    Bit-exact, cycle-accurate streaming model matching impulse_noise_filter.v.
    Matches line-buffer shift registers, window generation, 5-stage median pipeline,
    and threshold-based noise replacement.
    """
    H, W = image.shape
    N = H * W
    pixels = image.ravel().tolist()

    lb0 = [0] * W
    lb1 = [0] * W
    row_r = [0, 0, 0]
    row_m = [0, 0, 0]
    row_t = [0, 0, 0]

    FILL_LATENCY = W + 2
    MED_LATENCY = 5

    pipe_valid = [False] * MED_LATENCY
    pipe_centre = [0] * MED_LATENCY
    pipe_noisy = [False] * MED_LATENCY
    pipe_median = [0] * MED_LATENCY

    fill_cnt = 0
    pipeline_filled = False

    stream_in = pixels + [0] * (FILL_LATENCY + MED_LATENCY + 30)
    hw_out = []

    for px in stream_in:
        # Non-blocking assignment semantics:
        # 1. Sample state before posedge clk:
        win = list(row_t + row_m + row_r)
        centre = win[4]
        is_noisy = (centre == 0) or (centre == 255)
        med = int(np.median(win))

        if not pipeline_filled:
            if fill_cnt == FILL_LATENCY - 1:
                pipeline_filled = True
            else:
                fill_cnt += 1
        win_valid = pipeline_filled

        # 2. Output from pipeline (end of delay line):
        out_valid = pipe_valid[-1]
        out_centre = pipe_centre[-1]
        out_noisy = pipe_noisy[-1]
        out_med = pipe_median[-1]

        if out_valid and len(hw_out) < N:
            hw_out.append(out_med if out_noisy else out_centre)

        # 3. State update at posedge clk:
        pipe_valid = [win_valid] + pipe_valid[:-1]
        pipe_centre = [centre] + pipe_centre[:-1]
        pipe_noisy = [is_noisy] + pipe_noisy[:-1]
        pipe_median = [med] + pipe_median[:-1]

        lb0_out = lb0[-1]
        lb1_out = lb1[-1]
        lb0 = [px] + lb0[:-1]
        lb1 = [lb0_out] + lb1[:-1]
        row_r = [row_r[1], row_r[2], px]
        row_m = [row_m[1], row_m[2], lb0_out]
        row_t = [row_t[1], row_t[2], lb1_out]

    return np.array(hw_out, dtype=np.uint8).reshape(H, W)


def adaptive_median_filter(image: np.ndarray,
                            min_window: int = 3,
                            max_window: int = 7) -> np.ndarray:
    """Adaptive Median Filter (AMF) with window expansion from 3x3 to 7x7."""
    if image.ndim != 2:
        raise ValueError("Expected a 2-D grayscale image array.")
    if min_window % 2 == 0 or max_window % 2 == 0:
        raise ValueError("Window sizes must be odd.")

    H, W = image.shape
    half_max = max_window // 2
    padded = _pad_reflect(image, half_max)
    filtered = np.empty_like(image)

    for r in range(H):
        for c in range(W):
            pr, pc = r + half_max, c + half_max
            z_xy = int(image[r, c])
            win_size = min_window
            while win_size <= max_window:
                half = win_size // 2
                window = padded[pr-half:pr+half+1, pc-half:pc+half+1].ravel()
                z_min = int(window.min())
                z_max = int(window.max())
                z_med = int(np.median(window))
                if z_min < z_med < z_max:
                    if z_min < z_xy < z_max:
                        filtered[r, c] = z_xy
                    else:
                        filtered[r, c] = z_med
                    break
                else:
                    win_size += 2
            else:
                filtered[r, c] = z_med

    return filtered
