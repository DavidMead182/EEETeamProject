#!/usr/bin/env python3


import numpy as np
import matplotlib.pyplot as plt
from sys import argv

data = np.loadtxt(argv[1])

c = 0
for i, d in enumerate(data):
    distances = d[:9]
    strengths = d[9:18]
    for i in range(len(distances)):
        if strengths[i] < -10: distances[i] = 10000; c += 1

    sorted_distances = np.sort(distances)
    data[i] = np.concatenate((sorted_distances, d[9:]))


data = np.transpose(data) 

print(c / len(data[0])) 

print(np.min(data[-2]), np.max(data[-2]))

fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={'projection': 'polar'})
fig.tight_layout()

for d in data[:9]:
    ax.plot(-data[-2],d,".")
ax.set_rmax(7)
ax.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
ax.grid(True)

#plt.show()

plt.savefig(f"{argv[1]}.pdf")
