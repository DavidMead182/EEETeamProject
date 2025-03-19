import sys
import os

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtCore import Qt
from views.mainWindow import MainWindow
from views.minimapWindow import MinimapWindow
from views.noWindow import NoWindow
from PyQt5.QtGui import QPixmap

@pytest.fixture(scope="module")
def app():
    """Create a QApplication instance for testing"""
    return QApplication([])

@pytest.fixture
def main_window(qtbot):
    """Fixture to create the MainWindow instance."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

@pytest.fixture
def no_window(qtbot, main_window):
    """Fixture to create NoWindow instance."""
    window = NoWindow("No Page - Manual Setup", main_window.stack)
    qtbot.addWidget(window)
    return window

# @pytest.fixture
# def minimap_window(qtbot, main_window):
#     """Fixture to create MinimapWindow instance."""
#     dummy_pixmap = QPixmap(100, 100)  # Create a dummy pixmap for testing
#     window = MinimapWindow(dummy_pixmap, "test_path", main_window.stack)
#     qtbot.addWidget(window)
#     return window


def test_main_window_initialization(main_window):
    """Test if MainWindow initializes correctly."""
    assert main_window.windowTitle() == "Firefighter UAV"
    assert main_window.stack.count() == 3  # Ensure all pages are added


# def test_button_redirections(main_window, qtbot):
#     """Test redirection when clicking buttons."""
#     btn_no = main_window.findChild(QPushButton, "btnNo")
#     btn_yes = main_window.findChild(QPushButton, "btnYes")
    
#     assert btn_no is not None
#     assert btn_yes is not None
    
#     qtbot.mouseClick(btn_no, Qt.LeftButton)
#     assert main_window.stack.currentWidget() == main_window.noPage
    
#     qtbot.mouseCaick(btn_yes, Qt.LeftButton)
#     assert main_window.stack.currentWidget() == main_window.uploadPage


# def test_no_window_back_button(no_window, qtbot, main_window):
#     """Test if NoWindow back button returns to main window."""
#     btn_back = no_window.findChild(QPushButton, "Back")
#     qtbot.mouseClick(btn_back, Qt.LeftButton)
#     assert main_window.stack.currentIndex() == 0  # Should be back at main


# def test_minimap_window_ui(minimap_window):
#     """Test if MinimapWindow initializes properly."""
#     assert minimap_window.windowTitle() == "Firefighter UAV - Processed Page"
