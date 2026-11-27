"""
Generate a zero-padded SMF reference that matches the RTL boundary behaviour,
and update the testbench expected file accordingly.
"""
import numpy as np
from PIL import Image

W, H = 64, 64

def load_raw(path):
    with open(path) as f:
        return np.array([int(l.strip(), 16) for l in f if l.strip()], dtype=np.uint8)

def save_raw(arr, path):
    with open(path, "w") as f:
        for v in arr.ravel():
            f.write(f"{int(v):02x}\n")
    print(f"Saved: {path}  ({arr.size} bytes)")

def median_filter_zero_pad(image):
    """3x3 median filter with zero-padding (matches RTL line buffer init)."""
    H, W = image.shape
    padded = np.pad(image, 1, mode='constant', constant_values=0)
    out = np.empty_like(image)
    for r in range(H):
        for c in range(W):
            window = padded[r:r+3, c:c+3].ravel()
            out[r, c] = int(np.median(window))
    return out

noisy = load_raw("results/synthetic_noisy_10pct.raw").reshape(H, W)
smf_zero = median_filter_zero_pad(noisy)

save_raw(smf_zero, "results/synthetic_smf_10pct_zeropad.raw")
Image.fromarray(smf_zero).save("results/synthetic_smf_10pct_zeropad.png")
print("Zero-padded SMF reference generated.")
