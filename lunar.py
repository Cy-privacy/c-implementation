import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                            QVBoxLayout, QWidget, QProgressBar, QMessageBox,
                            QDoubleSpinBox, QDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import subprocess
import pkg_resources
import platform

class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initial Setup")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        # XY Sensitivity
        self.xy_label = QLabel("X-Axis and Y-Axis Sensitivity:")
        self.xy_spin = QDoubleSpinBox()
        self.xy_spin.setRange(0.1, 100.0)
        self.xy_spin.setSingleStep(0.1)
        self.xy_spin.setValue(6.9)
        
        # Targeting Sensitivity
        self.target_label = QLabel("Targeting Sensitivity:")
        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(0.1, 100.0)
        self.target_spin.setSingleStep(0.1)
        self.target_spin.setValue(6.9)
        
        # Save Button
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        
        layout.addWidget(self.xy_label)
        layout.addWidget(self.xy_spin)
        layout.addWidget(self.target_label)
        layout.addWidget(self.target_spin)
        layout.addWidget(self.save_btn)
        
        self.setLayout(layout)
    
    def save_settings(self):
        xy_sens = self.xy_spin.value()
        targeting_sens = self.target_spin.value()
        
        path = "lib/config"
        if not os.path.exists(path):
            os.makedirs(path)
            
        sensitivity_settings = {
            "xy_sens": xy_sens,
            "targeting_sens": targeting_sens,
            "xy_scale": 10/xy_sens,
            "targeting_scale": 1000/(targeting_sens * xy_sens)
        }
        
        with open('lib/config/config.json', 'w') as outfile:
            json.dump(sensitivity_settings, outfile)
            
        self.accept()

class DependencyInstaller(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        try:
            # Install requirements
            self.status.emit("Installing dependencies...")
            process = subprocess.Popen([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            if process.returncode != 0:
                self.error.emit(f"Error installing dependencies: {error.decode()}")
                return
                
            self.progress.emit(100)
            self.status.emit("Installation complete!")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lunar Vision")
        self.setFixedSize(500, 400)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title = QLabel("Lunar Vision")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("Ready to start")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Buttons
        self.install_btn = QPushButton("Install Dependencies")
        self.install_btn.clicked.connect(self.install_dependencies)
        layout.addWidget(self.install_btn)
        
        self.start_btn = QPushButton("Start Lunar Vision")
        self.start_btn.clicked.connect(self.start_lunar)
        layout.addWidget(self.start_btn)
        
        self.setup_btn = QPushButton("Configure Settings")
        self.setup_btn.clicked.connect(self.show_setup)
        layout.addWidget(self.setup_btn)
        
        # Check initial setup
        self.check_initial_setup()
        
    def check_initial_setup(self):
        if not os.path.exists("lib/config/config.json"):
            self.show_setup()
            
    def show_setup(self):
        dialog = SetupDialog(self)
        dialog.exec()
        
    def install_dependencies(self):
        self.progress.setVisible(True)
        self.install_btn.setEnabled(False)
        self.status_label.setText("Installing dependencies...")
        
        self.installer = DependencyInstaller()
        self.installer.progress.connect(self.progress.setValue)
        self.installer.status.connect(self.status_label.setText)
        self.installer.error.connect(self.show_error)
        self.installer.finished.connect(self.installation_complete)
        self.installer.start()
        
    def installation_complete(self):
        self.progress.setVisible(False)
        self.install_btn.setEnabled(True)
        self.status_label.setText("Ready to start!")
        
    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.progress.setVisible(False)
        self.install_btn.setEnabled(True)
        self.status_label.setText("Installation failed!")
        
    def start_lunar(self):
        try:
            from lib.aimbot import Aimbot
            self.lunar = Aimbot(collect_data=False)
            self.lunar.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start Lunar Vision: {str(e)}")

if __name__ == "__main__":
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())