#!/usr/bin/env python3

import sys, re, serial, argparse
import matplotlib.pyplot as plt
import matplotlib.animation as ani
from collections import defaultdict, deque
import numpy as np

# ── args ──────────────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("port"), ap.add_argument("baud", type=int)
args = ap.parse_args()

# ── serial ────────────────────────────────────────────────────────
ser = serial.Serial(args.port, args.baud, timeout=0.2)

# ── plotting boiler-plate ─────────────────────────────────────────
plt.style.use("fast")
fig=plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111)
ax.grid(which="both")
plt.ylabel("distance (m)")
plt.xlabel("time (ms)")

keep = 150
lines = []
dists = []
since_update = []
times = deque(maxlen=keep)
for i in range(5):
    since_update.append(0)
    dists.append(deque(maxlen=keep))
    dists[-1].append(0.0)

    line, = ax.plot([], [], label=f"peak {i}")
    lines.append(line)
ax.legend(fontsize="small", loc="upper left")

# ── update func ───────────────────────────────────────────────────
def update(_):
    global dists

    while ser.in_waiting:
        m=ser.readline().decode("ascii","ignore").split(",")
        if len(m) != 22: continue
        dists_now = list(map(float, m[4:9]))

        if len(times) == 0:
            times.append(int(m[3]))
        times.append(int(m[3]))

        sorted_dists = np.sort(dists_now)
        for d, sd in zip(dists, sorted_dists):
            if sd == 1e8: d.append(d[-1])
            else:         d.append(sd / 1000.0)
        

    for i in range(len(dists)):
        if since_update[i] >= keep: 
            n = len(dists[i])
            dists[i].clear()
            dists[i].extend(np.zeros(n))

    # plt.plot(range(len(dists)), dists)
    for line, dist in zip(lines, dists):
        line.set_data(times, dist)
    ax.relim()
    ax.autoscale_view()

    return dists

# ── keep a reference to avoid GC  (save_count disables the warning) ──
anim = ani.FuncAnimation(fig, update, interval=50, blit=False,
                         save_count=1, cache_frame_data=False)

plt.tight_layout(); plt.show()
