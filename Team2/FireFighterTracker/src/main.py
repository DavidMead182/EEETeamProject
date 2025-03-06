import sys
from PyQt5.QtWidgets import QApplication
from views.mainWindow import MainWindow
import os
import globalVaiables

if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.dirname(__file__))) 
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())
