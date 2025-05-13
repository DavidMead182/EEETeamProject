#!/usr/bin/env python3 

import matplotlib.pyplot as plt
import numpy as np
import sys

peaks = {}
data = np.loadtxt(sys.argv[1])

for d in data:
    if not d[0] in peaks:
        peaks[d[0]] = ([], [])

    peaks[d[0]][0].append(d[1])
    peaks[d[0]][1].append(d[3])

plt.figure()
for p, d in peaks.items():
    plt.plot(d[1], d[0])
plt.show()
