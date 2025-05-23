from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from widgets.titleWidget import TitleWidget

class RadarPage(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack
        self.setWindowTitle("Radar Visualisation")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("assets/icons/LOGO.png"))

        self.radar_data = None
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()

        # --- LEFT PANEL ---
        left_layout = QVBoxLayout()
        titleCard = TitleWidget("Radar Demonstration", "Rankine Rooms from Radar", "assets/images/SFRS Logo.png")
        left_layout.addWidget(titleCard)

        self.btn_load = QPushButton("Load Radar TSV File")
        self.btn_back = QPushButton("Back")

        for btn in [self.btn_load, self.btn_back]:
            btn.setFont(QFont("Arial", 12))
            left_layout.addWidget(btn, alignment=Qt.AlignCenter)
            left_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.btn_load.clicked.connect(self.load_radar_data)
        self.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # --- RIGHT PANEL (Radar Plot) ---
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.canvas)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        self.setLayout(layout)

        self.apply_stylesheet("assets/stylesheets/base.qss")

    def load_radar_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Radar TSV", "", "TSV Files (*.tsv *.txt)")
        if file_path:
            df = pd.read_csv(file_path, sep="\t", header=0)  # assuming headers: distance, heading
            df.columns = df.columns.str.strip().str.lower()
            self.radar_data = df
            self.plot_radar_frame()


    def plot_radar_frame(self):
        if self.radar_data is None:
            return

        self.ax.clear()

        df = self.radar_data.dropna(subset=["distance", "heading"])
        distances = pd.to_numeric(df["distance"], errors="coerce").to_numpy()
        headings = pd.to_numeric(df["heading"], errors="coerce").to_numpy()

        angles_rad = headings
        x = distances * np.cos(angles_rad)
        y = distances * np.sin(angles_rad)

        print("Distances:", distances[:5])
        print("Headings:", headings[:5])

        self.ax.scatter(x, y, c='blue', s=50)
        self.ax.set_aspect('equal')
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.set_title("Radar Point Cloud")
        self.ax.set_xlabel("X (m)")
        self.ax.set_ylabel("Y (m)")
        self.ax.grid(True)
        self.canvas.draw()

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")
