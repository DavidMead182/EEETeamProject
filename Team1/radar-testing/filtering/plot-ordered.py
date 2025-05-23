#!/usr/bin/env python3 

import matplotlib.pyplot as plt
import numpy as np
import sys

peaks = {}
data = np.loadtxt(sys.argv[1])

init_time = 0
current_peaks = []
for d in data:
    if init_time == 0:
        init_time = d[3]
    
    if d[0] == 0 and len(current_peaks) != 0:
        current_peaks = np.sort(current_peaks, axis=0)
        for cp in current_peaks:
            if cp[0] not in peaks: peaks[cp[0]] = [[], []]
            peaks[cp[0]][1].append(cp[3] - init_time)
            peaks[cp[0]][0].append(cp[1])

        current_peaks = []

    current_peaks.append(d) 

plt.figure(figsize=(10, 6), layout="constrained")
for p, d in peaks.items():
    d = np.array(d)
    plt.plot(d[1] / 1000.0, d[0] / 1000.0, label=f"peak {int(p + 1)}")
plt.legend(loc="upper left") 
plt.grid(which="both") 
plt.xlabel("time (s)") 
plt.ylabel("distance (m)")
plt.ylim(0, 7) 
plt.savefig(f"plots/{sys.argv[1]}-ordered.pdf")
