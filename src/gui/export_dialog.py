# src/gui/export_dialog.py

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QSpinBox, QProgressBar,
                             QFileDialog, QMessageBox, QFrame, QGroupBox,
                             QComboBox, QCheckBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from core.gif_exporter import GifExporter

class ModernGroupBox(QGroupBox):
    """Modern styled group box"""
    
    def __init__(self, title=""):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: white;
                border: 2px solid #0078d4;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #1e1e1e;
            }
        """)

class TimeSlider(QSlider):
    """Custom time slider with modern styling"""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal):
        super().__init__(orientation)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 2px solid #ffffff;
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -8px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #106ebe;
                border: 2px solid #ffffff;
            }
            QSlider::sub-page:horizontal {
                background: #0078d4;
                border-radius: 3px;
            }
        """)

class GifExportDialog(QDialog):
    """Dialog for exporting video segments as GIF"""
    
    # Signal to communicate with main window
    preview_frame_requested = pyqtSignal(float)  # Request frame at specific time
    
    def __init__(self, parent=None, video_path=None, duration_ms=0, current_position_ms=0):
        super().__init__(parent)
        self.video_path = video_path
        self.duration_ms = duration_ms
        self.current_position_ms = current_position_ms
        self.duration_seconds = duration_ms / 1000.0
        self.parent_window = parent
        
        # Export settings
        self.start_time = current_position_ms / 1000.0  # Start from current position
        self.end_time = min(self.start_time + 10, self.duration_seconds)  # Default 10 seconds or end of video
        self.gif_exporter = GifExporter()
        
        # Frame preview
        self.start_frame_pixmap = None
        self.end_frame_pixmap = None
        
        self.setup_ui()
        self.connect_signals()
        self.update_preview()
        self.load_frame_previews()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Export GIF")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QSpinBox, QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #0078d4;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #106ebe;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Export Video Segment as GIF")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Time selection group
        time_group = ModernGroupBox("Time Selection")
        time_layout = QVBoxLayout()
        
        # Current video info
        info_label = QLabel(f"Video Duration: {self.format_time(self.duration_seconds)}")
        info_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        time_layout.addWidget(info_label)
        
        # Start time
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start Time:"))
        
        self.start_slider = TimeSlider()
        self.start_slider.setMaximum(int(self.duration_seconds * 10))  # 0.1 second precision
        self.start_slider.setValue(int(self.start_time * 10))  # Start from current position
        start_layout.addWidget(self.start_slider)
        
        self.start_time_label = QLabel(self.format_time(self.start_time))
        self.start_time_label.setMinimumWidth(50)
        self.start_time_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        start_layout.addWidget(self.start_time_label)
        
        time_layout.addLayout(start_layout)
        
        # End time
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("End Time:"))
        
        self.end_slider = TimeSlider()
        self.end_slider.setMaximum(int(self.duration_seconds * 10))
        self.end_slider.setValue(int(self.end_time * 10))  # End time based on start + duration
        end_layout.addWidget(self.end_slider)
        
        self.end_time_label = QLabel(self.format_time(self.end_time))
        self.end_time_label.setMinimumWidth(50)
        self.end_time_label.setStyleSheet("color: #ff6b00; font-weight: bold;")
        end_layout.addWidget(self.end_time_label)
        
        time_layout.addLayout(end_layout)
        
        # Duration info
        duration = self.end_time - self.start_time
        self.duration_label = QLabel(f"Duration: {duration:.1f} seconds")
        self.duration_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        time_layout.addWidget(self.duration_label)
        
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)
        
        # Export settings group
        settings_group = ModernGroupBox("Export Settings")
        settings_layout = QGridLayout()
        
        # FPS setting
        settings_layout.addWidget(QLabel("Frame Rate (FPS):"), 0, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(5, 30)
        self.fps_spin.setValue(10)
        self.fps_spin.setSuffix(" fps")
        settings_layout.addWidget(self.fps_spin, 0, 1)
        
        # Size setting
        settings_layout.addWidget(QLabel("Size:"), 1, 0)
        self.size_combo = QComboBox()
        self.size_combo.addItems([
            "Small (320x180)",
            "Medium (480x270)", 
            "Large (640x360)",
            "HD (960x540)",
            "Original Size"
        ])
        self.size_combo.setCurrentText("Medium (480x270)")
        settings_layout.addWidget(self.size_combo, 1, 1)
        
        # Quality setting
        settings_layout.addWidget(QLabel("Quality:"), 2, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Low (Smaller file)",
            "Medium (Balanced)",
            "High (Larger file)"
        ])
        self.quality_combo.setCurrentText("Medium (Balanced)")
        settings_layout.addWidget(self.quality_combo, 2, 1)
        
        # Optimize checkbox
        self.optimize_check = QCheckBox("Optimize for web (smaller file size)")
        self.optimize_check.setChecked(True)
        settings_layout.addWidget(self.optimize_check, 3, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Preview group
        preview_group = ModernGroupBox("Frame Preview")
        preview_layout = QVBoxLayout()
        
        # Frame preview layout
        frames_layout = QHBoxLayout()
        
        # Start frame preview
        start_frame_layout = QVBoxLayout()
        start_frame_label = QLabel("Start Frame")
        start_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_frame_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        start_frame_layout.addWidget(start_frame_label)
        
        self.start_frame_preview = QLabel()
        self.start_frame_preview.setFixedSize(200, 112)  # 16:9 aspect ratio
        self.start_frame_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_frame_preview.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #0078d4;
                border-radius: 4px;
                color: #666666;
            }
        """)
        self.start_frame_preview.setText("Loading...")
        start_frame_layout.addWidget(self.start_frame_preview)
        
        # Jump to start button
        self.jump_to_start_btn = QPushButton("Jump to Start")
        self.jump_to_start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        start_frame_layout.addWidget(self.jump_to_start_btn)
        
        frames_layout.addLayout(start_frame_layout)
        
        # Arrow
        arrow_label = QLabel("→")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setStyleSheet("font-size: 24px; color: #ffffff; font-weight: bold;")
        frames_layout.addWidget(arrow_label)
        
        # End frame preview
        end_frame_layout = QVBoxLayout()
        end_frame_label = QLabel("End Frame")
        end_frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        end_frame_label.setStyleSheet("color: #ff6b00; font-weight: bold;")
        end_frame_layout.addWidget(end_frame_label)
        
        self.end_frame_preview = QLabel()
        self.end_frame_preview.setFixedSize(200, 112)  # 16:9 aspect ratio
        self.end_frame_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.end_frame_preview.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: 2px solid #ff6b00;
                border-radius: 4px;
                color: #666666;
            }
        """)
        self.end_frame_preview.setText("Loading...")
        end_frame_layout.addWidget(self.end_frame_preview)
        
        # Jump to end button
        self.jump_to_end_btn = QPushButton("Jump to End")
        self.jump_to_end_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b00;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e55a00;
            }
        """)
        end_frame_layout.addWidget(self.jump_to_end_btn)
        
        frames_layout.addLayout(end_frame_layout)
        
        preview_layout.addLayout(frames_layout)
        
        # File size estimation
        self.size_estimate_label = QLabel("Estimated file size: Calculating...")
        self.size_estimate_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
        preview_layout.addWidget(self.size_estimate_label)
        
        # Duration warning
        self.duration_warning_label = QLabel("")
        self.duration_warning_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        self.duration_warning_label.setVisible(False)
        preview_layout.addWidget(self.duration_warning_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export GIF")
        self.export_button.setMinimumHeight(40)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b00;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e55a00;
            }
        """)
        button_layout.addWidget(self.export_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(40)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def connect_signals(self):
        """Connect all signals"""
        self.start_slider.valueChanged.connect(self.on_start_changed)
        self.end_slider.valueChanged.connect(self.on_end_changed)
        self.fps_spin.valueChanged.connect(self.update_preview)
        self.size_combo.currentTextChanged.connect(self.update_preview)
        self.quality_combo.currentTextChanged.connect(self.update_preview)
        self.optimize_check.toggled.connect(self.update_preview)
        
        self.export_button.clicked.connect(self.start_export)
        self.cancel_button.clicked.connect(self.reject)
        
        # Jump buttons
        self.jump_to_start_btn.clicked.connect(self.jump_to_start)
        self.jump_to_end_btn.clicked.connect(self.jump_to_end)
        
        # GIF exporter signals
        self.gif_exporter.progress_updated.connect(self.update_progress)
        self.gif_exporter.export_finished.connect(self.on_export_finished)
        self.gif_exporter.export_failed.connect(self.on_export_failed)
        
    def on_start_changed(self, value):
        """Handle start time slider change"""
        self.start_time = value / 10.0  # Convert to seconds
        
        # Ensure start is before end
        if self.start_time >= self.end_time:
            self.end_time = min(self.duration_seconds, self.start_time + 1)
            self.end_slider.setValue(int(self.end_time * 10))
            
        self.update_time_labels()
        self.update_preview()
        self.load_start_frame_preview()
        
    def on_end_changed(self, value):
        """Handle end time slider change"""
        self.end_time = value / 10.0  # Convert to seconds
        
        # Ensure end is after start
        if self.end_time <= self.start_time:
            self.start_time = max(0, self.end_time - 1)
            self.start_slider.setValue(int(self.start_time * 10))
            
        self.update_time_labels()
        self.update_preview()
        self.load_end_frame_preview()
        
    def jump_to_start(self):
        """Jump main player to start time"""
        if self.parent_window and hasattr(self.parent_window, 'video_player'):
            start_ms = int(self.start_time * 1000)
            self.parent_window.video_player.seek_to_position(start_ms)
            
    def jump_to_end(self):
        """Jump main player to end time"""
        if self.parent_window and hasattr(self.parent_window, 'video_player'):
            end_ms = int(self.end_time * 1000)
            self.parent_window.video_player.seek_to_position(end_ms)
            
    def load_frame_previews(self):
        """Load both start and end frame previews"""
        self.load_start_frame_preview()
        self.load_end_frame_preview()
        
    def load_start_frame_preview(self):
        """Load preview of start frame"""
        if not self.video_path:
            return
            
        pixmap = self.extract_frame_at_time(self.start_time)
        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(200, 112, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.start_frame_preview.setPixmap(scaled_pixmap)
            self.start_frame_pixmap = pixmap
        else:
            self.start_frame_preview.setText("No Preview")
            
    def load_end_frame_preview(self):
        """Load preview of end frame"""
        if not self.video_path:
            return
            
        pixmap = self.extract_frame_at_time(self.end_time)
        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(200, 112, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.end_frame_preview.setPixmap(scaled_pixmap)
            self.end_frame_pixmap = pixmap
        else:
            self.end_frame_preview.setText("No Preview")
            
    def extract_frame_at_time(self, time_seconds):
        """Extract frame at specific time"""
        try:
            import cv2
            from core.frame_manager import FrameManager
            
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                return None
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            target_frame = int(time_seconds * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            
            cap.release()
            
            if ret:
                frame_manager = FrameManager()
                return frame_manager.convert_cv_to_qt(frame)
            return None
            
        except Exception as e:
            print(f"Error extracting frame: {e}")
            return None
        
    def update_time_labels(self):
        """Update time display labels"""
        self.start_time_label.setText(self.format_time(self.start_time))
        self.end_time_label.setText(self.format_time(self.end_time))
        
        duration = self.end_time - self.start_time
        self.duration_label.setText(f"Duration: {duration:.1f} seconds")
        
    def update_preview(self):
        """Update preview and size estimation"""
        if not self.video_path:
            return
            
        # Update time labels
        self.update_time_labels()
        
        # Get export settings
        width, height = self.get_export_dimensions()
        fps = self.fps_spin.value()
        duration = self.end_time - self.start_time
        
        # Duration warnings
        if duration > 30:
            self.duration_warning_label.setText("⚠️ Warning: GIFs longer than 30 seconds may be very large!")
            self.duration_warning_label.setVisible(True)
        elif duration > 15:
            self.duration_warning_label.setText("⚠️ Note: GIFs longer than 15 seconds may be large files")
            self.duration_warning_label.setVisible(True)
        else:
            self.duration_warning_label.setVisible(False)
        
        # Estimate file size
        estimated_size = self.gif_exporter.get_estimated_size(
            self.video_path, self.start_time, self.end_time, fps, width, height
        )
        
        size_text = self.gif_exporter.format_file_size(estimated_size)
        self.size_estimate_label.setText(f"Estimated file size: {size_text}")
        
        # Add quality recommendation
        if estimated_size > 50 * 1024 * 1024:  # 50MB
            self.size_estimate_label.setText(f"Estimated file size: {size_text} (Very Large! Consider reducing duration, size, or FPS)")
            self.size_estimate_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        elif estimated_size > 10 * 1024 * 1024:  # 10MB
            self.size_estimate_label.setText(f"Estimated file size: {size_text} (Large file - consider optimization)")
            self.size_estimate_label.setStyleSheet("color: #ff8800; font-weight: bold;")
        else:
            self.size_estimate_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        
    def get_export_dimensions(self):
        """Get export dimensions based on size setting"""
        size_text = self.size_combo.currentText()
        
        if "320x180" in size_text:
            return 320, 180
        elif "480x270" in size_text:
            return 480, 270
        elif "640x360" in size_text:
            return 640, 360
        elif "960x540" in size_text:
            return 960, 540
        else:  # Original size
            # TODO: Get original video dimensions
            return 640, 360
            
    def get_quality_setting(self):
        """Get quality setting"""
        quality_text = self.quality_combo.currentText()
        
        if "Low" in quality_text:
            return 70
        elif "Medium" in quality_text:
            return 85
        else:  # High
            return 95
            
    def start_export(self):
        """Start the GIF export process"""
        if not self.video_path:
            QMessageBox.warning(self, "Error", "No video loaded")
            return
            
        if self.end_time <= self.start_time:
            QMessageBox.warning(self, "Error", "End time must be after start time")
            return
            
        # Get output file path
        suggested_name = f"export_{int(self.start_time)}s-{int(self.end_time)}s.gif"
        output_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save GIF As", 
            suggested_name,
            "GIF Files (*.gif);;All Files (*)"
        )
        
        if not output_path:
            return
            
        # Setup export parameters
        width, height = self.get_export_dimensions()
        fps = self.fps_spin.value()
        quality = self.get_quality_setting()
        
        self.gif_exporter.setup_export(
            self.video_path, output_path, self.start_time, self.end_time,
            fps, width, height, quality
        )
        
        # Update UI for export
        self.export_button.setEnabled(False)
        self.export_button.setText("Exporting...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start export
        self.gif_exporter.start()
        
    def update_progress(self, progress):
        """Update export progress"""
        self.progress_bar.setValue(progress)
        
    def on_export_finished(self, output_path):
        """Handle successful export"""
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        self.export_button.setText("Export GIF")
        
        QMessageBox.information(
            self, 
            "Export Complete", 
            f"GIF exported successfully!\n\nSaved to: {output_path}"
        )
        
        self.accept()
        
    def on_export_failed(self, error_message):
        """Handle export failure"""
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        self.export_button.setText("Export GIF")
        
        QMessageBox.critical(self, "Export Failed", error_message)
        
    def format_time(self, seconds):
        """Format seconds as mm:ss"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"