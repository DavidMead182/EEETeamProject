#!/usr/bin/env python3

import sys, re, serial, argparse
import matplotlib.pyplot as plt
import matplotlib.animation as ani
from collections import defaultdict, deque
import numpy as np
from filter import Filter

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

keep = 50
lines = []
dists = []
dists_filtered = []
since_update = []
iir_filters = []
times = deque(maxlen=keep)
for i in range(5):
    since_update.append(0)
    dists.append(deque(maxlen=keep))
    dists[-1].append(0.0)

    dists_filtered.append(deque(maxlen=keep))
    dists_filtered[-1].append(0.0)

    line, = ax.plot([], [], label=f"peak {i}")
    lines.append(line)
    line, = ax.plot([], [], "--", color=line.get_color(), label=f"peak {i} filtered")
    lines.append(line)

    iir_filters.append(Filter(10, 2.5))

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
        i = 0
        for d, df, f, sd in zip(dists, dists_filtered, iir_filters, sorted_dists):
            if sd == 1e8: d.append(d[-1]);       since_update[i] += 1
            else:         d.append(sd / 1000.0); since_update[i]  = 0 
            
            df.append(f.filter(d[-1]))
            i += 1
        

    for i in range(len(dists)):
        if since_update[i] >= keep: 
            n = len(dists[i])
            dists[i].clear()
            dists_filtered[i].clear()
            dists[i].extend(np.zeros(n))
            dists_filtered[i].extend(np.zeros(n))

    for i in range(len(dists)):
        lines[i*2].set_data(times, dists[i])
        lines[i*2 + 1].set_data(times, dists_filtered[i])

#    for line, dist in zip(lines, dists):
#        line.set_data(times, dist)
    ax.relim()
    ax.autoscale_view()

    return dists

# ── keep a reference to avoid GC  (save_count disables the warning) ──
anim = ani.FuncAnimation(fig, update, interval=50, blit=False,
                         save_count=1, cache_frame_data=False)

plt.tight_layout(); plt.show()
