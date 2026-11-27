"""
Analyse the mismatch between DUT output and software SMF reference.
Prints a spatial map showing where differences occur.
"""
import numpy as np
from PIL import Image

W, H = 64, 64
N = W * H

def load_raw(path):
    with open(path) as f:
        return np.array([int(l.strip(), 16) for l in f if l.strip()], dtype=np.uint8)

dut  = load_raw("../rtl/sim_out/dut_output.raw")
smf  = load_raw("results/synthetic_smf_10pct.raw")
orig = load_raw("results/synthetic_original.raw")
noisy= load_raw("results/synthetic_noisy_10pct.raw")

assert len(dut) == N and len(smf) == N

diff = (dut != smf).reshape(H, W).astype(np.uint8)
total_mismatch = diff.sum()
print(f"Total mismatches: {total_mismatch} / {N}  ({100*total_mismatch/N:.1f}%)")

# Which rows have mismatches?
row_counts = diff.sum(axis=1)
print("\nMismatch count per row:")
for r, cnt in enumerate(row_counts):
    if cnt > 0:
        print(f"  Row {r:3d}: {cnt} mismatches")

# Are mismatches confined to border pixels?
interior = diff[1:-1, 1:-1]
border = total_mismatch - interior.sum()
print(f"\nBorder mismatches  : {border}")
print(f"Interior mismatches: {interior.sum()}")

# Sample a few mismatch pixels
print("\nSample mismatches (row, col):")
coords = np.argwhere(diff)
for r, c in coords[:15]:
    print(f"  [{r:2d},{c:2d}]  noisy={noisy[r*W+c]:3d}  dut={dut[r*W+c]:3d}  smf={smf[r*W+c]:3d}  orig={orig[r*W+c]:3d}")

# Save diff image for visual inspection
diff_vis = diff * 255
Image.fromarray(diff_vis).save("results/mismatch_map.png")
print("\nMismatch map saved to results/mismatch_map.png")
