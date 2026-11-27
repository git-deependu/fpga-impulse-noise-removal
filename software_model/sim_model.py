"""
Simulate the RTL window generator and impulse_noise_filter logic in Python
to verify the expected behaviour pixel-by-pixel, and compare against the
actual DUT output.
"""
import numpy as np
from collections import deque
from PIL import Image

W, H = 64, 64
N = W * H

def load_raw(path):
    with open(path) as f:
        return np.array([int(l.strip(), 16) for l in f if l.strip()], dtype=np.uint8)

noisy  = load_raw("results/synthetic_noisy_10pct.raw")
smf_sw = load_raw("results/synthetic_smf_10pct.raw")
dut    = load_raw("../rtl/sim_out/dut_output.raw")

# ─── RTL-accurate window generator model ────────────────────────────────────
# line_buffer: shift-register of depth W
# row_r[0..2], row_m[0..2], row_t[0..2]
# lb0: delays by W cycles; lb1: delays by 2W cycles
# After filling (2W+2 clocks), emit one window per input pixel.
#
# Window layout per RTL:
#   [0][1][2]  ← row_t  (oldest: 2 rows ago)
#   [3][4][5]  ← row_m  (1 row ago), [4] = centre
#   [6][7][8]  ← row_r  (current)

def simulate_rtl(pixels):
    """Simulate the window_generator + impulse_noise_filter in Python."""
    # Line buffers as deques of length W
    lb0 = deque([0]*W, maxlen=W)
    lb1 = deque([0]*W, maxlen=W)
    # Horizontal shift registers (oldest at [0], newest at [2])
    row_r = [0, 0, 0]
    row_m = [0, 0, 0]
    row_t = [0, 0, 0]

    fill_cnt = 0
    pipeline_filled = False
    outputs = []

    FILL_LATENCY = 2 * W + 2
    MED_LATENCY = 4

    # Delay chains for centre pixel and noisy flag
    centre_delay = deque([0]*MED_LATENCY, maxlen=MED_LATENCY)
    noisy_delay  = deque([False]*MED_LATENCY, maxlen=MED_LATENCY)
    # Median pipeline delay (we can compute median instantly in Python)
    median_delay = deque([0]*MED_LATENCY, maxlen=MED_LATENCY)
    valid_pipe   = deque([False]*MED_LATENCY, maxlen=MED_LATENCY)

    for px in pixels:
        # Line buffer update (lb0 gets current pixel, lb1 gets lb0 output)
        lb0_out = lb0[-1]   # oldest (delayed by W cycles) - deque: left=oldest
        lb1_out = lb1[-1]
        lb1.appendleft(lb0_out)
        lb0.appendleft(px)

        # Shift row registers
        row_r = [row_r[1], row_r[2], px]
        row_m = [row_m[1], row_m[2], lb0_out]
        row_t = [row_t[1], row_t[2], lb1_out]

        # Fill counter
        if not pipeline_filled:
            if fill_cnt == FILL_LATENCY - 1:
                pipeline_filled = True
            else:
                fill_cnt += 1

        win_valid = pipeline_filled

        # Window: [row_t[0..2], row_m[0..2], row_r[0..2]]
        window = row_t + row_m + row_r
        centre = row_m[1]   # win[4]
        noisy_flag = (centre == 0) or (centre == 255)
        med = int(np.median(window))

        # Push into delay chains (always advancing)
        # Stage 0 only captures when win_valid
        if win_valid:
            centre_delay.appendleft(centre)
            noisy_delay.appendleft(noisy_flag)
            median_delay.appendleft(med)
        valid_pipe.appendleft(win_valid)

        # Output from delay chains
        out_valid = valid_pipe[-1]
        if out_valid:
            c = centre_delay[-1]
            n = noisy_delay[-1]
            m = median_delay[-1]
            out_pixel = m if n else c
            outputs.append(out_pixel)

    return np.array(outputs, dtype=np.uint8)

# Run extended input (N + drain pixels)
drain = 2*W + 10
input_seq = noisy.tolist() + [0]*drain
rtl_sim = simulate_rtl(input_seq)[:N]

print(f"RTL-simulated outputs: {len(rtl_sim)}")

# Compare sim vs DUT
sim_vs_dut  = np.sum(rtl_sim != dut[:len(rtl_sim)])
sim_vs_smf  = np.sum(rtl_sim != smf_sw[:len(rtl_sim)])
print(f"RTL-sim vs DUT hardware : {sim_vs_dut} mismatches")
print(f"RTL-sim vs Python SMF   : {sim_vs_smf} mismatches")

# Show first few sim outputs vs smf vs dut
print("\nFirst 10 pixels comparison:")
print(f"{'idx':>5}  {'noisy':>6}  {'sim':>5}  {'dut':>5}  {'smf':>5}")
for i in range(10):
    print(f"{i:5d}  {noisy[i]:6d}  {rtl_sim[i]:5d}  {dut[i]:5d}  {smf_sw[i]:5d}")
