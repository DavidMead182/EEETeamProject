import numpy as np
import pandas as pd
import time
from collections import deque
import matplotlib.pyplot as plt

# === Load CSV Data ===
filename = 'Walk_test_a2.csv'
data = pd.read_csv(filename)

# === Extract time and 3-axis accelerometer data ===
time_data = data.iloc[:, 1].to_numpy()      # Time column
acc_data = data.iloc[:, 8:11].to_numpy()    # X, Y, Z accel columns

# === Infer sampling rate from time column ===
dt = np.mean(np.diff(time_data))
sample_rate = 1.0 / dt

# === Parameters ===
window_size = 80         # ZUPT window size
smooth_size = 10          # Smoothing window
threshold = 0.6          # ZUPT Mahalanobis threshold

# === Buffers ===
acc_buffer = deque(maxlen=smooth_size)
signal_window = deque(maxlen=window_size)
velocity_zupt = [0]
position_zupt = [0]

velocity_nozupt = [0]
position_nozupt = [0]

accumulated_drift_with_zupt = []
accumulated_drift_without_zupt = []
zupt_flags = [] 

# === Real-Time Plot Setup (Optional) ===
plt.ion()

t_vals, acc_vals, zupt_vals, pos_vals = [], [], [], []

accumulated_drift_with_zupt = []
accumulated_drift_without_zupt = []

fig, axs = plt.subplots(3, 1, figsize=(10, 10))  # 3 subplots now

axs[0].set_title("Acceleration Magnitude with ZUPT Detection")
axs[0].set_ylabel("Acceleration (m/s²)")

axs[1].set_title("Position Estimate with ZUPT")
axs[1].set_ylabel("Position (m)")

axs[2].set_title("Accumulated Drift Error")
axs[2].set_ylabel("Drift (m)")
axs[2].set_xlabel("Time (s)")

# Reuse existing:
acc_plot, = axs[0].plot([], [], 'b', label='Acceleration')
zupt_plot, = axs[0].plot([], [], 'r--', label='ZUPT')

pos_plot, = axs[1].plot([], [], 'g', label='Position Estimate')

# New:
drift_plot_zupt, = axs[2].plot([], [], 'm', label='Accumulated Drift with ZUPT')
drift_plot_nozupt, = axs[2].plot([], [], 'c--', label='Accumulated Drift without ZUPT')


# === Define streaming function from CSV ===
def get_next_acceleration(index):
    if index < len(acc_data):
        return acc_data[index]
    else:
        return None  # End of data

# === Simulated Real-Time Loop ===
for i in range(len(acc_data)):
    accel = get_next_acceleration(i)
    if accel is None:
        break

    x, y, z = accel
    t = time_data[i]
    
    print(data.columns)
    print(data.iloc[:, 8:11].head())

    # === Compute acceleration magnitude ===
    acc_mag = np.linalg.norm([x, y, z])

    # === Smoothing ===
    acc_buffer.append(acc_mag)
    acc_smooth = np.mean(acc_buffer)

    # === ZUPT Detection ===
    signal_window.append(acc_smooth)
    mu = np.mean(signal_window)
    sigma = np.var(signal_window)
    mahal_dist = (acc_smooth - mu) / np.sqrt(sigma) if sigma > 0 else 0
    zupt = abs(mahal_dist) < threshold
    zupt_flags.append(zupt)
    
    # ZUPT-based velocity: zero acceleration if ZUPT
    acc_val = 0 if zupt else acc_smooth
    v_zupt = velocity_zupt[-1] + acc_val * dt
    p_zupt = position_zupt[-1] + v_zupt * dt
    velocity_zupt.append(v_zupt)
    position_zupt.append(p_zupt)

    # No ZUPT (use raw smoothed acceleration always)
    v_nozupt = velocity_nozupt[-1] + acc_smooth * dt
    p_nozupt = position_nozupt[-1] + v_nozupt * dt
    velocity_nozupt.append(v_nozupt)
    position_nozupt.append(p_nozupt)

    # True position baseline is zero
    drift_zupt = abs(p_zupt - position_zupt[0])
    drift_nozupt = abs(p_nozupt - position_nozupt[0])
    accumulated_drift_with_zupt.append(
        accumulated_drift_with_zupt[-1] + drift_zupt if accumulated_drift_with_zupt else drift_zupt
        )
    accumulated_drift_without_zupt.append(
        accumulated_drift_without_zupt[-1] + drift_nozupt if accumulated_drift_without_zupt else drift_nozupt
        )

    # === Update time and values ===
    t_vals.append(t)
    acc_vals.append(acc_smooth)
    zupt_vals.append(acc_smooth if zupt else np.nan)

    # === Trim to shortest array length ===
    min_len = min(len(t_vals), len(position_zupt), len(accumulated_drift_with_zupt), len(accumulated_drift_without_zupt))

    t_vals_trimmed = t_vals[:min_len]
    acc_vals_trimmed = acc_vals[:min_len]
    zupt_vals_trimmed = zupt_vals[:min_len]
    position_zupt_trimmed = position_zupt[:min_len]
    accum_drift_with_zupt_trimmed = accumulated_drift_with_zupt[:min_len]
    accum_drift_without_zupt_trimmed = accumulated_drift_without_zupt[:min_len]

    # === Update Plots with trimmed data ===
    acc_plot.set_data(t_vals_trimmed, acc_vals_trimmed)
    zupt_plot.set_data(t_vals_trimmed, zupt_vals_trimmed)
    pos_plot.set_data(t_vals_trimmed, position_zupt_trimmed)
    drift_plot_zupt.set_data(t_vals_trimmed, accum_drift_with_zupt_trimmed)
    drift_plot_nozupt.set_data(t_vals_trimmed, accum_drift_without_zupt_trimmed)

    for ax in axs:
        ax.relim()
        ax.autoscale_view()

    plt.pause(dt)

plt.ioff()
plt.show()