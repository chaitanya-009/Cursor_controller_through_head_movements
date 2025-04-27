#main.py 
import sys
import os
if sys.platform == "darwin":
    os.environ["QT_MAC_DISABLE_CONSOLE"] = "1"  # Hide terminal
    if getattr(sys, 'frozen', False):
        os.environ["QT_MAC_WANTS_LAYER"] = "1"
from PyQt6.QtWidgets import QApplication
from gui.os_selection import OSSelectionWindow
from gui.control_window import ControlWindow

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.os_window = OSSelectionWindow()
        self.control_window = None
        
        self.os_window.os_selected.connect(self.show_control_window)
        self.os_window.show()
        
        sys.exit(self.app.exec())

    def show_control_window(self, os_type):
        self.control_window = ControlWindow(os_type)
        self.control_window.show()
        self.os_window.close()  # Close the OS selection window

if __name__ == "__main__":
    AppController()