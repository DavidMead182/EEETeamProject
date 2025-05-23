from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from widgets.titleWidget import TitleWidget

from scipy.ndimage import uniform_filter1d
from scipy.integrate import cumulative_trapezoid as cumtrapz
import numpy as np


class DeadReckoningPage(QWidget):
    def __init__(self, stack, text="None"):
        super().__init__()
        self.stack = stack
        self.setWindowTitle("Firefighter Tracker - IMU Visualisation")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("assets/icons/LOGO.png"))

        self.imu_data = []
        self.positions = []
        self.current_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()

        # --- LEFT PANEL ---
        left_layout = QVBoxLayout()
        titleCard = TitleWidget("IMU Demonstration", "Dead reckoning from accelerometer", "assets/images/SFRS Logo.png")
        left_layout.addWidget(titleCard)

        self.btn_load = QPushButton("Load IMU Data File")
        self.btn_start = QPushButton("Start Animation")
        self.btn_reset = QPushButton("Reset Animation")
        self.btn_back = QPushButton("Back")

        for btn in [self.btn_load, self.btn_start, self.btn_reset, self.btn_back]:
            btn.setFont(QFont("Arial", 12))
            left_layout.addWidget(btn, alignment=Qt.AlignCenter)
            left_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.btn_load.clicked.connect(self.load_data)
        self.btn_start.clicked.connect(self.start_animation)
        self.btn_reset.clicked.connect(self.reset_animation)
        self.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.progress_label = QLabel("Step: 0 / 0")
        self.progress_label.setFont(QFont("Arial", 10))
        left_layout.addWidget(self.progress_label, alignment=Qt.AlignCenter)

        # --- RIGHT PANEL ---
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        self.accel_figure, (self.ax_ax, self.ax_ay) = plt.subplots(2, 1, figsize=(5, 3))
        self.accel_canvas = FigureCanvas(self.accel_figure)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.canvas)
        right_layout.addWidget(self.accel_canvas)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        self.setLayout(layout)

        self.apply_stylesheet("assets/stylesheets/base.qss")

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open IMU Data File", "", "Text Files (*.txt)")
        if file_path:
            self.imu_data = self.parse_imu_file(file_path)
            self.current_index = 0
            self.reset_animation()

    def parse_imu_file(self, filepath):
        imu_data = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        parts = list(map(float, line.strip().split()))
                        if len(parts) == 10:
                            imu_data.append({
                                "xr": parts[1],
                                "yr": parts[2],
                                "zr": parts[3],
                                "xa": parts[4],
                                "ya": parts[5],
                                "za": parts[6],
                                "roll": parts[7],
                                "pitch": parts[8],
                                "yaw": parts[9],
                            })
                    except ValueError:
                        print(f"Skipping line: {line.strip()}")
        return imu_data

    def start_animation(self):
        if not self.imu_data:
            return
        self.positions = [(0, 0)]
        self.velocity = [0.0, 0.0]
        self.x_accel_history = []
        self.y_accel_history = []
        self.time_history = []
        self.current_index = 0
        self.timer.start(100)  # 10 Hz = 0.1s


    def update_plot(self):
        if self.current_index >= len(self.imu_data):
            self.timer.stop()
            return

        dt = 0.005  # 10 Hz

        data = self.imu_data[self.current_index]

        g_to_mps2 = 9.81
        ax = (data["xa"] - 1.0) * 9.81
        ay = (data["ya"] - 1.0) * 9.81


        # # Track acceleration history
        # if len(self.x_accel_history) > 10:
        #     ax -= np.mean(self.x_accel_history[-10:]) * g_to_mps2
        #     ay -= np.mean(self.y_accel_history[-10:]) * g_to_mps2

        self.time_history.append(self.current_index * dt)
        self.x_accel_history.append(ax)
        self.y_accel_history.append(ay)

        # Integrate velocity
        self.velocity[0] += ax * dt
        self.velocity[1] += ay * dt

        # Integrate position
        last_pos = self.positions[-1]
        new_x = last_pos[0] + self.velocity[0] * dt + 0.5 * ax * dt ** 2
        new_y = last_pos[1] + self.velocity[1] * dt + 0.5 * ay * dt ** 2
        self.positions.append((new_x, new_y))

        # Update trajectory plot
        self.ax.clear()
        x_vals = [p[0] for p in self.positions]
        y_vals = [p[1] for p in self.positions]
        self.ax.plot(x_vals, y_vals, marker='o', label="Path (meters)")
        self.ax.set_title("IMU Dead Reckoning Trajectory")
        self.ax.set_xlabel("X Position (m)")
        self.ax.set_ylabel("Y Position (m)")
        self.ax.grid(True)
        self.ax.legend()

        # Compute ZUPT-based X and Y positions
        x_zupt = self.compute_zupt_positions(self.x_accel_history, dt)
        y_zupt = self.compute_zupt_positions(self.y_accel_history, dt)

        # Plot original and ZUPT-corrected
        self.ax.plot(x_vals, y_vals, marker='o', label="Dead Reckoning", color="blue")
        self.ax.plot(x_zupt, y_zupt, linestyle='--', label="ZUPT Enhanced", color="red")
        self.ax.set_title("IMU Dead Reckoning Trajectory")
        self.ax.set_xlabel("X Position (mm)")
        self.ax.set_ylabel("Y Position (mm)")
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()

        self.canvas.draw()

        # Update acceleration plots
        self.ax_ax.clear()
        self.ax_ax.plot(self.time_history, self.x_accel_history, label="Ax (m/s²)", color='r')
        self.ax_ax.set_ylabel("Ax")
        self.ax_ax.grid(True)

        self.ax_ay.clear()
        self.ax_ay.plot(self.time_history, self.y_accel_history, label="Ay (m/s²)", color='b')
        self.ax_ay.set_ylabel("Ay")
        self.ax_ay.set_xlabel("Time (s)")
        self.ax_ay.grid(True)

        self.accel_canvas.draw()

        # Update step counter
        self.current_index += 1
        self.progress_label.setText(f"Step: {self.current_index} / {len(self.imu_data)}")



    def reset_animation(self):
        self.timer.stop()
        self.positions = []
        self.current_index = 0
        self.velocity = [0.0, 0.0]
        self.ax.clear()
        self.ax.set_title("IMU Dead Reckoning Trajectory")
        self.ax.set_xlabel("X Position (meters)")
        self.ax.set_ylabel("Y Position (meters)")
        self.ax.grid(True)
        self.canvas.draw()
        self.progress_label.setText(f"Step: 0 / {len(self.imu_data)}")

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")

    def compute_zupt_positions(self, accel_series, dt, window_size=10, threshold=0.6):
        acc_signal = uniform_filter1d(np.array(accel_series), size=5)
        zupt = np.zeros_like(acc_signal, dtype=bool)

        # ZUPT detection via Mahalanobis-style thresholding
        for i in range(window_size, len(acc_signal)):
            window = acc_signal[i - window_size:i]
            mu = np.mean(window)
            sigma = np.var(window)
            if sigma > 0:
                dist = (acc_signal[i] - mu) / np.sqrt(sigma)
            else:
                dist = 0
            if abs(dist) < threshold:
                zupt[i] = True

        # Integration with ZUPT
        velocity = cumtrapz(acc_signal, dx=dt, initial=0)
        velocity[zupt] = 0
        position = cumtrapz(velocity, dx=dt, initial=0)
        return position