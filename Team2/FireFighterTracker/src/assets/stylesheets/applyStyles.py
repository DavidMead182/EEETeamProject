def apply_stylesheet(self, filename):
    try:
        with open(filename, "r") as f:
            self.setStyleSheet(f.read())
        print("Log: Stylesheet applied.")
    except FileNotFoundError:
        print("Log: Stylesheet not found. Using default styles.")