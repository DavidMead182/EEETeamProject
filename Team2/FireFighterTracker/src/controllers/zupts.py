import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid as cumtrapz
from scipy.ndimage import uniform_filter1d

# === Load CSV File ===
filename = 'Walk_test_a2.csv'  # Replace with your actual filename
data = pd.read_csv(filename)

# === Extract Time and Acceleration ===
t = data.iloc[:, 1].to_numpy()  # Time column
acc_raw = data.iloc[:, 8:10].to_numpy()  # Accel X, Y, Z

# === Sampling Info ===
dt = np.mean(np.diff(t))
fs = 1 / dt

# === Process Acceleration ===
acc_true = np.linalg.norm(acc_raw, axis=1)  # Magnitude
acc_drift = 5
acc_noise = acc_drift * np.random.randn(len(acc_true))
acc_signal = acc_true + acc_noise
acc_signal = uniform_filter1d(acc_signal, size=5)  # Smooth signal

# === ZUPT Detection (Mahalanobis Distance) ===
window_size = 80
zupt = np.zeros_like(acc_signal, dtype=bool)

for i in range(window_size, len(acc_signal)):
    window_data = acc_signal[i - window_size:i]
    mu = np.mean(window_data)
    sigma = np.var(window_data)
    mahal_dist = (acc_signal[i] - mu) / np.sqrt(sigma) if sigma > 0 else 0
    if abs(mahal_dist) < 0.6:
        zupt[i] = True

# === Integrate to Get Velocity and Position ===
velocity = cumtrapz(acc_signal, t, initial=0)
velocity_no_zupt = velocity.copy()
velocity[zupt] = 0

position_with_zupt = cumtrapz(velocity, t, initial=0)
position_without_zupt = cumtrapz(velocity_no_zupt, t, initial=0)

# === True Position Unknown (Zero Baseline) ===
true_position = np.zeros_like(position_with_zupt)
drift_error_with_zupt = position_with_zupt - true_position
drift_error_without_zupt = position_without_zupt - true_position

accumulated_drift_with_zupt = np.cumsum(np.abs(drift_error_with_zupt))
accumulated_drift_without_zupt = np.cumsum(np.abs(drift_error_without_zupt))

# === Plot Results ===
plt.figure(figsize=(10, 12))

plt.subplot(3, 1, 1)
plt.plot(t, acc_signal, 'b', label='Acceleration')
plt.plot(t, zupt * max(acc_signal), 'r--', label='ZUPT Detected')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration (m/s²)')
plt.title('Accelerometer Data & ZUPT Detection')
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(t, position_with_zupt, 'g', label='Position with ZUPT')
plt.plot(t, position_without_zupt, 'b--', label='Position without ZUPT')
plt.xlabel('Time (s)')
plt.ylabel('Position (m)')
plt.title('Estimated Position')
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(t, accumulated_drift_with_zupt, 'm', label='Accumulated Drift with ZUPT')
plt.plot(t, accumulated_drift_without_zupt, 'c--', label='Accumulated Drift without ZUPT')
plt.xlabel('Time (s)')
plt.ylabel('Accumulated Drift Error (m)')
plt.title('Accumulated Drift Error')
plt.legend()

plt.tight_layout()
plt.show()