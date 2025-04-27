# gui/control_window.py
import cv2
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton,QDoubleSpinBox, QLabel, QGroupBox, QGridLayout, 
                            QMessageBox,QCheckBox,QFormLayout,QDialogButtonBox,QDialog, QFrame,QSlider, QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QImage, QPixmap, QColor, QPainter
from gui.workers import CameraWorker
from config.settings import load_config, save_config

class ControlWindow(QMainWindow):
    def __init__(self, selected_os, parent=None):
        super().__init__(parent)
        self.selected_os = selected_os
        self.config = load_config()
        self.worker = None
        self.thread = None
        self.init_ui()
        self.setWindowTitle(f"AI Cursor Control - {self.selected_os.capitalize()}")
    
    def handle_config_update(self, new_config):
        """Update components with new configuration"""
        self.config = new_config
        if self.worker:
            self.worker.head_tracker.config = new_config
            self.worker.blink_detector.config = new_config

    def init_ui(self):
        self.setMinimumSize(1000, 800)
        self.setStyleSheet("""
            background-color: #2d2d2d;
            color: #ffffff;
            font-family: 'Arial';
        """)

        # Main container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Left Panel (Camera and Status)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        # Camera Preview
        camera_frame = QFrame()
        camera_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 2px solid #3d3d3d;
            }
        """)
        camera_layout = QVBoxLayout(camera_frame)
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: black;")
        self.camera_label.setFixedSize(640, 480)
        camera_layout.addWidget(self.camera_label)
        left_layout.addWidget(camera_frame)

        # Status Panel
        status_group = QGroupBox("System Status")
        status_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                color: #88c0d0;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        status_layout = QGridLayout(status_group)
        self.status_labels = {
            'cursor': self._create_status_label("Cursor Position", "0, 0"),
            'movement': self._create_status_label("Head Movement", "Calibrating..."),
            'blink': self._create_status_label("Blink Detection", "Active"),
            'fps': self._create_status_label("Processing FPS", "60")
        }
        for i, (key, (title, value)) in enumerate(self.status_labels.items()):
            status_layout.addWidget(title, i, 0)
            status_layout.addWidget(value, i, 1)
        left_layout.addWidget(status_group)
        main_layout.addWidget(left_panel, 70)

        # Right Panel (Controls)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)
        # Control Group
        control_group = QGroupBox("Controls")
        control_group.setStyleSheet(status_group.styleSheet())
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(15)

        # Main Control Button
        self.control_btn = QPushButton("START TRACKING")
        self.control_btn.setFixedHeight(60)
        self.control_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #219a52; }
        """)
        self.control_btn.clicked.connect(self.toggle_start_stop)
        control_layout.addWidget(self.control_btn)

        # Secondary Controls
        controls = [
            ("Calibrate System", "#3498db", self.calibrate_system),
            ("Settings", "#9b59b6", self.open_settings),
            ("Help Guide", "#f1c40f", self.show_help),
            ("Exit", "#e74c3c", self.close)
        ]
        for text, color, handler in controls:
            btn = QPushButton(text)
            btn.setFixedHeight(45)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-size: 14px;
                    border-radius: 6px;
                }}
                QPushButton:hover {{ background-color: {self._darken_color(color)}; }}
            """)
            btn.clicked.connect(handler)
            control_layout.addWidget(btn)

        control_layout.addStretch()
        right_layout.addWidget(control_group)
        main_layout.addWidget(right_panel, 30)

    # Helper methods
    def _create_status_label(self, title, initial):
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #88c0d0;")
        value_label = QLabel(initial)
        value_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            padding: 5px 0;
        """)
        return (title_label, value_label)

    def _darken_color(self, hex_color, factor=0.8):
        rgb = [int(hex_color[i+1:i+3], 16) for i in (0, 2, 4)]
        return f"#{hex(int(rgb[0]*factor))[2:]}{hex(int(rgb[1]*factor))[2:]}{hex(int(rgb[2]*factor))[2:]}"

    def toggle_start_stop(self):
        if self.control_btn.text() == "START TRACKING":
            self.start_processing()
        else:
            self.stop_processing()

    def start_processing(self):
        try:
            self.worker = CameraWorker(self.config, self.selected_os)
            self.thread = QThread()
            
            self.worker.moveToThread(self.thread)
            self.worker.frame_processed.connect(self.update_frame)
            self.worker.error_occurred.connect(self.show_error)
            
            self.thread.started.connect(self.worker.start_processing)
            self.thread.start()
            
            self.control_btn.setText("STOP TRACKING")
            self.control_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #c82333; }
                QPushButton:pressed { background-color: #bd2130; }
            """)
            
        except Exception as e:
            self.show_error(f"Initialization Error: {str(e)}")
            self.stop_processing()

    def stop_processing(self):
        if self.worker:
            self.worker.stop_processing()
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            
        self.control_btn.setText("START TRACKING")
        self.control_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #219a52; }
        """)

    def update_frame(self, frame, x, y, action):
        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            qt_image = QImage(rgb_image.data, w, h, QImage.Format.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))
            
            
            self.status_labels['cursor'][1].setText(f"{int(x)}, {int(y)}")
            
        except Exception as e:
            self.show_error(f"Display Error: {str(e)}")

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def calibrate_system(self):
        QMessageBox.information(self, "Calibration", 
            "Please look directly at the camera and blink twice to calibrate")

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.settings_tabs.config_updated.connect(self.handle_config_update)
        
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            
            pass
        else:
            
            pass
    
    def show_help(self):
        QMessageBox.information(self, "Help Guide",
            "Official documentation: \nhttps://example.com/help\n\n"
            "Keyboard Shortcuts:\n"
            "- Space: Toggle tracking\n"
            "- Esc: Exit application")

    def closeEvent(self, event):
        self.stop_processing()
        event.accept()
        
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration Settings")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            background-color: #2d2d2d;
            color: #ffffff;
            font-family: 'Arial';
        """)
        
        
        self.settings_tabs = SettingsTabs()
        
        # Dialog buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.settings_tabs)
        layout.addWidget(btn_box)
        self.setLayout(layout)

class SettingsTabs(QWidget):
    config_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Head Tracking Section
        head_group = QGroupBox("Head Tracking")
        head_layout = QFormLayout()
        
        
        self.cursor_acceleration = self._create_slider(
            "Cursor Acceleration", 
            self.config['head_tracking']['cursor_acceleration'], 
            1.0, 3.0, 0.1,
            display_transform=lambda v: f"{v:.1f}x"
        )
        self.deadzone_size = self._create_slider(
            "Deadzone Size", 
            self.config['head_tracking']['deadzone_size'], 
            0.0, 0.2, 0.01,
            display_transform=lambda v: f"{v:.2f}"
        )
        self.response_curve = self._create_slider(
            "Response Curve", 
            self.config['head_tracking']['response_curve'], 
            1.0, 3.0, 0.1,
            display_transform=lambda v: f"{v:.1f}"
        )
        
        head_layout.addRow(self.cursor_acceleration['label'], self.cursor_acceleration['slider'])
        head_layout.addRow(self.deadzone_size['label'], self.deadzone_size['slider'])
        head_layout.addRow(self.response_curve['label'], self.response_curve['slider'])
        head_group.setLayout(head_layout)
        layout.addWidget(head_group)

        # Blink Detection Section
        blink_group = QGroupBox("Blink Detection")
        blink_layout = QFormLayout()
        
        
        self.blink_cooldown = self._create_slider(
            "Blink Cooldown", 
            self.config['blink_detection']['cooldown'], 
            0.1, 1.0, 0.1,
            display_transform=lambda v: f"{v:.1f}s"
        )
        self.eye_sanity_check = QCheckBox()
        self.eye_sanity_check.setChecked(self.config['blink_detection']['enable_sanity_check'])
        self.eye_sanity_check.stateChanged.connect(
            lambda s: self.update_config('blink_detection', 'enable_sanity_check', bool(s))
        )
        
        blink_layout.addRow(self.blink_cooldown['label'], self.blink_cooldown['slider'])
        blink_layout.addRow("Enable Eye Sanity Check:", self.eye_sanity_check)
        blink_group.setLayout(blink_layout)
        layout.addWidget(blink_group)

        # Cursor Actions Section
        action_group = QGroupBox("Cursor Actions")
        action_layout = QFormLayout()
        
        self.click_hold_duration = self._create_slider(
            "Click Hold Duration", 
            self.config['actions']['click_hold_duration'], 
            0.1, 1.5, 0.1,
            display_transform=lambda v: f"{v:.1f}s"
        )
        self.drag_threshold = self._create_slider(
            "Drag Threshold", 
            self.config['actions']['drag_threshold'], 
            10, 100, 1,
            display_transform=lambda v: f"{v}px"
        )
        
        action_layout.addRow(self.click_hold_duration['label'], self.click_hold_duration['slider'])
        action_layout.addRow(self.drag_threshold['label'], self.drag_threshold['slider'])
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)

        
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QFormLayout()
        
        self.kalman_process_noise = self._create_slider(
            "Kalman Process Noise", 
            self.config['advanced']['kalman_process_noise'], 
            0.001, 0.1, 0.001,
            display_transform=lambda v: f"{v:.3f}"
        )
        self.kalman_measurement_noise = self._create_slider(
            "Kalman Measurement Noise", 
            self.config['advanced']['kalman_measurement_noise'], 
            1, 10, 0.1,
            display_transform=lambda v: f"{v:.1f}"
        )
        
        advanced_layout.addRow(self.kalman_process_noise['label'], self.kalman_process_noise['slider'])
        advanced_layout.addRow(self.kalman_measurement_noise['label'], self.kalman_measurement_noise['slider'])
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        self.setLayout(layout)

    def _create_slider(self, label_text, initial, min_val, max_val, step, display_transform=None):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        value_label = QLabel()
        slider = QSlider(Qt.Orientation.Horizontal)
        
        
        if isinstance(initial, float):
            scale = 1000 if step < 0.01 else 100
        else:
            scale = 1
        
        slider.setRange(int(min_val * scale), int(max_val * scale))
        slider.setValue(int(initial * scale))
        slider.setSingleStep(int(step * scale))
        
        def update_value(value):
            actual_value = value / scale
            if display_transform:
                value_label.setText(display_transform(actual_value))
            else:
                value_label.setText(f"{actual_value:.2f}")
            self.update_config_from_slider(label_text, actual_value)
        
        slider.valueChanged.connect(update_value)
        update_value(slider.value())
        
        layout.addWidget(label)
        layout.addWidget(slider)
        layout.addWidget(value_label)
        
        return {
            'container': container,
            'label': label,
            'slider': slider,
            'value_label': value_label
        }

    def update_config_from_slider(self, label, value):
        mapping = {
            "Cursor Acceleration": ('head_tracking', 'cursor_acceleration'),
            "Deadzone Size": ('head_tracking', 'deadzone_size'),
            "Response Curve": ('head_tracking', 'response_curve'),
            "Blink Cooldown": ('blink_detection', 'cooldown'),
            "Click Hold Duration": ('actions', 'click_hold_duration'),
            "Drag Threshold": ('actions', 'drag_threshold'),
            "Kalman Process Noise": ('advanced', 'kalman_process_noise'),
            "Kalman Measurement Noise": ('advanced', 'kalman_measurement_noise')
        }
        
        if label in mapping:
            section, key = mapping[label]
            self.config[section][key] = value
            save_config(self.config)
            self.config_updated.emit(self.config)
        
        
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    window = ControlWindow("macOS")
    window.show()
    app.exec()