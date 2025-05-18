#!/usr/bin/env python3 

import matplotlib.pyplot as plt
import numpy as np
import sys
from collections import deque

peaks = {}
data = np.loadtxt(sys.argv[1])

def insert_into(dq, d):
    rotations = 0
    while d >= dq[0] and rotations <= len(dq): 
        dq.rotate(-1)
        rotations += 1

    dq.appendleft(d)
    dq.rotate(rotations)

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

avg = [deque([0] * 5) for i in range(5)]

plt.figure(figsize=(10, 6), layout="constrained")
for p, d in peaks.items():
    median_filtered = np.zeros(len(d[0]))

    for i, di in enumerate(d[0]):
        insert_into(avg[int(p)], di)
        median_filtered[i] = avg[int(p)][2]

    d = np.array(d)
    
    line, = plt.plot(d[1] / 1000.0, d[0] / 1000.0, label=f"peak {int(p + 1)}")
    plt.plot(d[1] / 1000.0, median_filtered / 1000.0, "--", color=line.get_color())
plt.legend(loc="upper left") 
plt.grid(which="both") 
plt.xlabel("time (s)") 
plt.ylabel("distance (m)")
plt.ylim(0, 7) 
plt.savefig(f"plots/{sys.argv[1]}-median.pdf")
