import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import cumtrapz
from scipy.ndimage import uniform_filter1d

# === Simulation Parameters ===
fs = 100  # Hz
dt = 1 / fs
t = np.arange(0, 10, dt)

# === Simulated Acceleration ===
acc_true = np.zeros_like(t)
acc_true[100:400] = 0.5     # accelerate for 3s
acc_true[400:600] = 0       # coast for 2s
acc_true[600:900] = -0.5    # decelerate for 3s

# === True Velocity and Position (for ground truth) ===
true_velocity = cumtrapz(acc_true, t, initial=0)
true_position = cumtrapz(true_velocity, t, initial=0)

# === Simulate IMU Signal with Noise ===
acc_drift = 5
acc_noise = acc_drift * np.random.randn(len(acc_true))
acc_signal = acc_true + acc_noise
acc_signal = uniform_filter1d(acc_signal, size=5)  # smooth noise

# === ZUPT Detection using Mahalanobis distance ===
window_size = 80
zupt = np.zeros_like(acc_signal, dtype=bool)

for i in range(window_size, len(acc_signal)):
    window_data = acc_signal[i - window_size:i]
    mu = np.mean(window_data)
    sigma = np.var(window_data)
    if sigma > 0:
        mahal_dist = (acc_signal[i] - mu) / np.sqrt(sigma)
    else:
        mahal_dist = 0
    if abs(mahal_dist) < 0.6:
        zupt[i] = True

# === Integration ===
velocity = cumtrapz(acc_signal, t, initial=0)
velocity_no_zupt = velocity.copy()
velocity[zupt] = 0  # Apply ZUPT

position_with_zupt = cumtrapz(velocity, t, initial=0)
position_without_zupt = cumtrapz(velocity_no_zupt, t, initial=0)

# === Drift Error ===
drift_error_with_zupt = position_with_zupt - true_position
drift_error_without_zupt = position_without_zupt - true_position

accumulated_drift_with_zupt = np.cumsum(np.abs(drift_error_with_zupt))
accumulated_drift_without_zupt = np.cumsum(np.abs(drift_error_without_zupt))

# === Plotting ===
plt.figure(figsize=(10, 12))

plt.subplot(3, 1, 1)
plt.plot(t, acc_signal, label="Measured Acceleration")
plt.plot(t, acc_true, label="True Acceleration")
plt.plot(t, zupt * np.max(acc_signal), 'r--', label="ZUPT Detected")
plt.title("Accelerometer Signal and ZUPT Detection")
plt.xlabel("Time (s)")
plt.ylabel("Acceleration (m/s²)")
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(t, position_with_zupt, label="Position with ZUPT")
plt.plot(t, position_without_zupt, label="Position without ZUPT", linestyle='--')
plt.plot(t, true_position, label="True Position", linestyle='-.')
plt.title("Estimated Position vs True Position")
plt.xlabel("Time (s)")
plt.ylabel("Position (m)")
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(t, accumulated_drift_with_zupt, label="Drift with ZUPT")
plt.plot(t, accumulated_drift_without_zupt, label="Drift without ZUPT", linestyle='--')
plt.title("Accumulated Drift Error")
plt.xlabel("Time (s)")
plt.ylabel("Drift (m)")
plt.legend()

plt.tight_layout()
plt.show()