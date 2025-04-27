import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty,pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QBrush

class OSButton(QPushButton):
    
    def __init__(self, icon_name, parent=None):
        super().__init__(parent)
        # Initialize animation properties
        self._border_width = 2
        self._selection_progress = 0.0
        self._click_progress = 0.0
        self._is_selected = False
        self._base_color = QColor(245, 245, 245)
        self._highlight_color = QColor(230, 240, 255)
        self._border_color = QColor(200, 200, 200)
        self._selected_border_color = QColor(14, 122, 254)
        
        self.setFixedSize(300, 300)
        self.setStyleSheet("background: transparent; border: none;")
        
        # Centered icon layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        # Transparent icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_icon(icon_name)
        layout.addWidget(self.icon_label)
        
        # Animation setup
        self.selection_anim = QPropertyAnimation(self, b"selectionProgress")
        self.selection_anim.setDuration(300)
        self.selection_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.click_anim = QPropertyAnimation(self, b"clickProgress")
        self.click_anim.setDuration(150)
        self.click_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def load_icon(self, name):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        
        img_path = os.path.join(base_path, "images", f"{name}.png")
        
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
        else:
            pixmap = self.create_fallback_icon()
            
        self.icon_label.setPixmap(pixmap.scaled(
            200, 200, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def create_fallback_icon(self):
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        painter.end()
        return pixmap

    # Animation properties
    def get_selection_progress(self):
        return self._selection_progress

    def set_selection_progress(self, value):
        self._selection_progress = value
        self.update()

    selectionProgress = pyqtProperty(float, get_selection_progress, set_selection_progress)

    def get_click_progress(self):
        return self._click_progress

    def set_click_progress(self, value):
        self._click_progress = value
        self.update()

    clickProgress = pyqtProperty(float, get_click_progress, set_click_progress)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate animated values
        current_bg = self._highlight_color if self._is_selected else self._base_color
        current_border = self._selected_border_color if self._is_selected else self._border_color
        
        # Apply click animation
        if self._click_progress > 0:
            current_bg = current_bg.darker(100 + int(10 * self._click_progress))
        
        # Draw background
        painter.setBrush(QBrush(current_bg))
        painter.setPen(QPen(current_border, 2 + 2 * self._selection_progress))
        painter.drawRoundedRect(10, 10, self.width()-20, self.height()-20, 12, 12)
        
        # Draw selection glow
        if self._is_selected:
            painter.setPen(QPen(QColor(14, 122, 254, 100), 6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(8, 8, self.width()-16, self.height()-16, 14, 14)

    def set_selected(self, selected):
        self._is_selected = selected
        self.selection_anim.stop()
        self.selection_anim.setStartValue(self._selection_progress)
        self.selection_anim.setEndValue(1.0 if selected else 0.0)
        self.selection_anim.start()

    def mousePressEvent(self, event):
        self.click_anim.stop()
        self.click_anim.setStartValue(0)
        self.click_anim.setEndValue(1)
        self.click_anim.start()
        super().mousePressEvent(event)

class OSSelectionWindow(QMainWindow):
    os_selected = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.selected_os = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("AI Cursor Control")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("background-color: #f8f9fa;")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        main_layout.setContentsMargins(40, 60, 40, 40)
        main_layout.setSpacing(40)
        
        # Button container
        button_frame = QFrame()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(60)
        button_layout.setContentsMargins(20, 20, 20, 20)
        button_frame.setLayout(button_layout)
        
        # Windows Button
        self.win_btn = OSButton("windows_logo")
        self.win_btn.clicked.connect(lambda: self.handle_os_select("windows"))
        button_layout.addWidget(self.win_btn)
        
        # Mac Button
        self.mac_btn = OSButton("mac_logo")
        self.mac_btn.clicked.connect(lambda: self.handle_os_select("mac"))
        button_layout.addWidget(self.mac_btn)
        
        main_layout.addWidget(button_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Continue Button
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setFixedSize(240, 50)
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #0e7afe;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 500;
                border: 2px solid #0e7afe;
                padding: 8px 24px;
            }
            QPushButton:disabled {
                color: #a0a0a0;
                border-color: #d0d0d0;
            }
            QPushButton:hover:enabled {
                background-color: #f0f7ff;
            }
            QPushButton:pressed:enabled {
                background-color: #e0f0ff;
            }
        """)
        self.continue_btn.clicked.connect(self.handle_continue)
        main_layout.addWidget(self.continue_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def handle_os_select(self, os_name):
        self.selected_os = os_name
        self.continue_btn.setEnabled(True)
        
        # Update button states
        self.win_btn.set_selected(os_name == "windows")
        self.mac_btn.set_selected(os_name == "mac")

    def handle_continue(self):
        if self.selected_os:
            self.os_selected.emit(self.selected_os)
            self.close()
        print(f"Selected OS: {self.selected_os}")
        # Add your window transition logic here

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    
    window = OSSelectionWindow()
    window.show()
    sys.exit(app.exec())