"""
Verify the 25-CAS comparator network produces the correct median for 9 values.
"""
import numpy as np

def cas(a, b):
    return min(a,b), max(a,b)

def sort_network_9(p):
    """Replicate the exact CAS sequence from median_filter_3x3.v"""
    p = list(p)

    # Stage 1 - 12 CAS
    p[0],p[1] = cas(p[0],p[1])
    p[3],p[4] = cas(p[3],p[4])
    p[6],p[7] = cas(p[6],p[7])
    p[1],p[2] = cas(p[1],p[2])
    p[4],p[5] = cas(p[4],p[5])
    p[7],p[8] = cas(p[7],p[8])
    p[0],p[1] = cas(p[0],p[1])
    p[3],p[4] = cas(p[3],p[4])
    p[6],p[7] = cas(p[6],p[7])
    p[0],p[3] = cas(p[0],p[3])
    p[3],p[6] = cas(p[3],p[6])
    p[0],p[3] = cas(p[0],p[3])

    # Stage 2 - 8 CAS
    p[1],p[4] = cas(p[1],p[4])
    p[4],p[7] = cas(p[4],p[7])
    p[1],p[4] = cas(p[1],p[4])
    p[2],p[5] = cas(p[2],p[5])
    p[5],p[8] = cas(p[5],p[8])
    p[2],p[5] = cas(p[2],p[5])
    p[2],p[4] = cas(p[2],p[4])
    p[4],p[6] = cas(p[4],p[6])

    # Stage 3 - 4 CAS
    p[2],p[4] = cas(p[2],p[4])
    p[3],p[4] = cas(p[3],p[4])
    p[4],p[5] = cas(p[4],p[5])
    p[4],p[6] = cas(p[4],p[6])

    # Stage 4 - 1 CAS
    p[3],p[4] = cas(p[3],p[4])

    return p

rng = np.random.default_rng(99)
errors = 0
N_TESTS = 100000
for _ in range(N_TESTS):
    vals = rng.integers(0, 256, 9).tolist()
    result = sort_network_9(vals)
    expected_median = int(np.median(vals))
    if result[4] != expected_median:
        errors += 1
        print(f"WRONG: {sorted(vals)} -> network[4]={result[4]}, expected={expected_median}")
        if errors >= 5:
            break

if errors == 0:
    print(f"CAS network correct on all {N_TESTS} random tests. median = index [4]")
else:
    print(f"ERRORS: {errors} failures")
