#!/usr/bin/env python3


import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt("log.dat")

for i, d in enumerate(data):
    distances = d[:9]
    sorted_distances = np.sort(distances)
    data[i] = np.concatenate((sorted_distances, d[9:]))

data = np.transpose(data) 

print(np.min(data[-2]), np.max(data[-2]))

fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
#ax.plot(-data[-2],data[2],".")

for d in data[:9]:
    ax.plot(-data[-2],d,".")
ax.set_rmax(7)
ax.set_rticks([0.5, 1, 1.5, 2])  # Less radial ticks
ax.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
ax.grid(True)

ax.set_title("A line plot on a polar axis", va='bottom')
plt.show()
