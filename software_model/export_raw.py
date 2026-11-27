"""
export_raw.py
-------------
Exports PNG images as raw 8-bit hex text files (one byte per line, no header)
compatible with Verilog $readmemh().

Usage
-----
    python export_raw.py --image results/synthetic_noisy_10pct.png
    python export_raw.py --dir results/               # exports all PNGs in dir
"""

import argparse
import os
import numpy as np
from PIL import Image


def png_to_hex(png_path: str, out_path: str | None = None) -> str:
    """Convert a grayscale PNG to a $readmemh-compatible hex text file."""
    img = Image.open(png_path).convert("L")
    arr = np.array(img, dtype=np.uint8)

    if out_path is None:
        out_path = os.path.splitext(png_path)[0] + ".raw"

    with open(out_path, "w") as f:
        for pixel in arr.ravel():
            f.write(f"{pixel:02x}\n")

    print(f"[+] {png_path}  ->  {out_path}  ({arr.size} bytes)")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Export PNG images to raw hex files for Verilog $readmemh."
    )
    parser.add_argument("--image", type=str, default=None,
                        help="Single PNG file to convert.")
    parser.add_argument("--dir", type=str, default=None,
                        help="Directory — convert all *.png files inside.")
    args = parser.parse_args()

    if args.image:
        png_to_hex(args.image)
    elif args.dir:
        for fname in sorted(os.listdir(args.dir)):
            if fname.lower().endswith(".png"):
                png_to_hex(os.path.join(args.dir, fname))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
