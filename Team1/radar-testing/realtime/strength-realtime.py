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
plt.xlabel("distance (m)")
plt.ylabel("strength")
ax.set_xlim(0, 7.0)
ax.set_ylim(-40, 40)

keep = 20
lines = []
dists = []
since_update = []
times = deque(maxlen=keep)
for i in range(5):
    since_update.append(0)
    dists.append(deque(maxlen=keep))
    # dists[-1].append(np.array([0.0, 0.0]))

    line, = ax.plot([1], [1], 'x', label=f"peak {i}")
    lines.append(line)
ax.legend(fontsize="small", loc="upper right")


# ── update func ───────────────────────────────────────────────────
def update(_):
    global dists

    while ser.in_waiting:
        line = ser.readline().decode("ascii","ignore")
        #print(line, end="")
        m=line.split("\t")
        if len(m) != 20: continue
        dists_now = list(map(lambda x: float(x) / 1000.0, m[1:10]))
        strengths_now = list(map(int, m[10:19]))

        #print(list(zip(dists_now, strengths_now)), file=sys.stderr)

        if len(times) == 0:
            times.append(int(m[0]))
        times.append(int(m[0]))

        for d, dn, sn in zip(dists, dists_now, strengths_now):
            if   dn == 1e6 and len(d) > 0: d.append(d[-1])
            elif dn == 1e6 or sn < -40000: d.append([0, 0])
            else:                          d.append([dn, sn / 1000.0])
        
        

    for i in range(len(dists)):
        if since_update[i] >= keep: 
            n = len(dists[i])
            dists[i].clear()
            dists[i].extend(np.zeros(n))

    if len(dists[0]) > 6:
        print("\b" * 1000, end="", file=sys.stderr)
        print("strength: {:09f}   distance: {:09f}".format( dists[0][-1][1], dists[0][-1][0]), end="", file=sys.stderr)
    sys.stderr.flush()
    for line, dist in zip(lines, dists):
        if len(dist) == 0: continue

        line.set_data(np.transpose(dist)[0], np.abs(np.transpose(dist)[1]))
    ax.relim()
    ax.autoscale_view()

    return dists

# ── keep a reference to avoid GC  (save_count disables the warning) ──
anim = ani.FuncAnimation(fig, update, interval=50, blit=False,
                         save_count=1, cache_frame_data=False)

plt.tight_layout(); plt.show()
