#!/usr/bin/env python3 

import matplotlib.pyplot as plt
import numpy as np
import sys

peaks = {}
data = np.loadtxt(sys.argv[1])

init_time = 0
for d in data:
    if not d[0] in peaks:
        peaks[d[0]] = ([], [])

    if init_time == 0:
        init_time = d[3]
    peaks[d[0]][0].append(d[1])
    peaks[d[0]][1].append(d[3] - init_time)

plt.figure(figsize=(10, 6), layout="constrained")
for p, d in peaks.items():
    d = np.array(d)
    plt.plot(d[1] / 1000.0, d[0] / 1000.0, label=f"peak {int(p + 1)}")
plt.legend(loc="upper left") 
plt.grid(which="both") 
plt.xlabel("time (s)") 
plt.ylabel("distance (m)")
plt.savefig(f"plots/{sys.argv[1]}.pdf")
