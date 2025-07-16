# src/gui/main_window.py

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QSlider, QFrame, QSizePolicy,
                             QApplication, QFileDialog, QGraphicsDropShadowEffect,
                             QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QPen, QBrush

# Import our video engine
from core.video_player import VideoPlayerEngine
from core.frame_manager import FrameManager
from .export_dialog import GifExportDialog

class VideoWidget(QLabel):
    """Custom video display widget (original design)"""
    
    # Signal to communicate with main window
    file_dropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 450)
        self.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: none;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        
        # Ensure widget can receive mouse events
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        
        # Initialize with placeholder
        self.show_placeholder()
        
        print("VideoWidget initialized with drag/drop and mouse tracking")  # Debug
        
    def show_placeholder(self):
        """Show placeholder text"""
        self.setText("Drop video files here or click to open")
        
        # Set font for the placeholder text
        font = QFont("Segoe UI", 14)
        font.setWeight(QFont.Weight.Light)
        self.setFont(font)
        
        # Style the placeholder text
        self.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border: none;
                color: #666666;
            }
        """)
        
    def display_frame(self, pixmap):
        """Display a video frame"""
        if pixmap and not pixmap.isNull():
            # Scale to fit widget while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
            
            # Update stylesheet to remove placeholder styling
            self.setStyleSheet("""
                QLabel {
                    background-color: #000000;
                    border: none;
                }
            """)
        else:
            self.show_placeholder()
    
    def dragEnterEvent(self, event):
        print("Drag enter event")  # Debug
        if event.mimeData().hasUrls():
            print("Accepting drag event")  # Debug
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        print("Drop event triggered")  # Debug
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        print(f"Dropped files: {files}")  # Debug
        if files:
            # Emit signal with the file path
            self.file_dropped.emit(files[0])
            
    def mousePressEvent(self, event):
        """Handle mouse clicks to open file dialog"""
        print("Mouse press event on video widget")  # Debug
        if event.button() == Qt.MouseButton.LeftButton:
            print("Left mouse button clicked")  # Debug
            self.file_dropped.emit("")  # Empty string signals to open dialog

class ModernButton(QPushButton):
    """Modern styled button with hover effects"""
    
    def __init__(self, text="", icon_path=None, size=40):
        super().__init__(text)
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(45, 45, 45, 0.8);
                border: none;
                border-radius: {size//2}px;
                color: white;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 120, 212, 0.9);
                border: 2px solid rgba(0, 120, 212, 0.5);
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 120, 212, 1.0);
            }}
        """)
        
        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

class ModernSlider(QSlider):
    """Custom styled slider for timeline"""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal):
        super().__init__(orientation)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: none;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #106ebe;
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -8px 0;
            }
            QSlider::sub-page:horizontal {
                background: #0078d4;
                border-radius: 2px;
            }
        """)

class ControlsWidget(QWidget):
    """Controls widget (always visible)"""
    
    play_pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int)  # Position in ms
    frame_step_requested = pyqtSignal(int)  # -1 for previous, 1 for next
    volume_changed = pyqtSignal(int)
    export_gif_requested = pyqtSignal()  # GIF export requested
    
    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.duration_ms = 0
        self.position_ms = 0
        self.seeking = False  # Initialize seeking flag
        self.seek_timer = QTimer()  # Timer for throttled seeking
        self.seek_timer.setSingleShot(True)
        self.seek_timer.timeout.connect(self.perform_delayed_seek)
        self.pending_seek_position = 0
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Spacer to push controls to bottom
        layout.addStretch()
        
        # Timeline container
        timeline_frame = QFrame()
        timeline_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 0.9);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        timeline_layout = QVBoxLayout(timeline_frame)
        timeline_layout.setSpacing(15)
        
        # Progress slider
        self.progress_slider = ModernSlider()
        self.progress_slider.setMaximum(100)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self.progress_slider.valueChanged.connect(self.on_slider_value_changed)
        timeline_layout.addWidget(self.progress_slider)
        
        # Controls row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)  # Increased spacing for better balance
        
        # Left side controls group
        left_controls = QHBoxLayout()
        left_controls.setSpacing(15)
        
        # Play/Pause button
        self.play_btn = ModernButton("▶", size=50)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        left_controls.addWidget(self.play_btn)
        
        # Stop button
        self.stop_btn = ModernButton("◼", size=45)  # Slightly larger for balance
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        left_controls.addWidget(self.stop_btn)
        
        # Frame navigation buttons
        self.prev_frame_btn = ModernButton("⏮", size=42)  # Slightly larger
        self.prev_frame_btn.clicked.connect(lambda: self.on_frame_step_clicked(-1))
        self.next_frame_btn = ModernButton("⏭", size=42)  # Slightly larger
        self.next_frame_btn.clicked.connect(lambda: self.on_frame_step_clicked(1))
        left_controls.addWidget(self.prev_frame_btn)
        left_controls.addWidget(self.next_frame_btn)
        
        controls_layout.addLayout(left_controls)
        
        # Center - Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: 600;
                min-width: 140px;
                text-align: center;
            }
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.time_label)
        
        # Right side controls group
        right_controls = QHBoxLayout()
        right_controls.setSpacing(15)
        
        # Volume controls
        self.volume_btn = ModernButton("🔊", size=42)
        self.volume_btn.clicked.connect(self.toggle_mute)  # Add mute functionality
        
        self.volume_slider = ModernSlider()
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)  # Default volume
        self.volume_slider.setFixedWidth(120)  # Slightly wider
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        
        # Store original volume for mute/unmute
        self.previous_volume = 70
        self.is_muted = False
        
        right_controls.addWidget(self.volume_btn)
        right_controls.addWidget(self.volume_slider)
        
        # GIF export button
        self.export_btn = ModernButton("GIF", size=45)  # Slightly larger
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 165, 0, 0.8);
                border: none;
                border-radius: 22px;
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 165, 0, 1.0);
            }
            QPushButton:disabled {
                background-color: rgba(100, 100, 100, 0.5);
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.export_btn.clicked.connect(self.on_export_gif_clicked)
        right_controls.addWidget(self.export_btn)
        
        # Fullscreen button
        self.fullscreen_btn = ModernButton("⛶", size=42)
        right_controls.addWidget(self.fullscreen_btn)
        
        controls_layout.addLayout(right_controls)
        
        timeline_layout.addLayout(controls_layout)
        layout.addWidget(timeline_frame)
        
        self.setLayout(layout)
        
        # Set initial background to transparent (like original overlay)
        self.setStyleSheet("background-color: transparent;")
        
        # Initialize export button as disabled
        self.update_export_button(False)
        
    def toggle_play_pause(self):
        """Toggle play/pause state"""
        self.is_playing = not self.is_playing
        self.play_btn.setText("⏸" if self.is_playing else "▶")
        self.play_pause_clicked.emit()
        
    def on_stop_clicked(self):
        """Handle stop button click"""
        self.is_playing = False
        self.play_btn.setText("▶")
        self.stop_clicked.emit()
        
    def on_frame_step_clicked(self, direction):
        """Handle frame step button clicks"""
        print(f"Frame step button clicked: {direction}")  # Debug
        self.frame_step_requested.emit(direction)
        
    def on_export_gif_clicked(self):
        """Handle GIF export button click"""
        print("GIF export button clicked")  # Debug
        self.export_gif_requested.emit()
        
    def toggle_mute(self):
        """Toggle mute/unmute"""
        if self.is_muted:
            # Unmute - restore previous volume
            self.volume_slider.setValue(self.previous_volume)
            self.volume_btn.setText("🔊")
            self.is_muted = False
        else:
            # Mute - save current volume and set to 0
            self.previous_volume = self.volume_slider.value()
            self.volume_slider.setValue(0)
            self.volume_btn.setText("🔇")
            self.is_muted = True
            
    def on_volume_changed(self, volume):
        """Handle volume slider changes"""
        # Update mute button icon based on volume level
        if volume == 0:
            self.volume_btn.setText("🔇")
            self.is_muted = True
        elif volume < 50:
            self.volume_btn.setText("🔉")
            self.is_muted = False
        else:
            self.volume_btn.setText("🔊")
            self.is_muted = False
            
        # If volume is changed manually, update previous volume for mute
        if not self.is_muted:
            self.previous_volume = volume
            
        # Emit signal to video player
        self.volume_changed.emit(volume)
        
    def update_export_button(self, enabled=True):
        """Update export button state"""
        self.export_btn.setEnabled(enabled)
        if enabled:
            self.export_btn.setToolTip("Export current segment as GIF")
        else:
            self.export_btn.setToolTip("Load a video first")
        
    def on_slider_pressed(self):
        """Handle when user starts dragging slider"""
        print("Slider pressed")  # Debug
        self.seeking = True
        
    def on_slider_released(self):
        """Handle when user releases slider"""
        print("Slider released")  # Debug
        self.seeking = False
        
        # Stop the seek timer
        self.seek_timer.stop()
        
        # Perform final seek to exact position if needed
        if self.duration_ms > 0:
            final_position_ms = int((self.progress_slider.value() / 100.0) * self.duration_ms)
            print(f"Final seek to: {final_position_ms}ms")  # Debug
            self.seek_requested.emit(final_position_ms)
            
    def on_slider_value_changed(self, value):
        """Handle slider value changes - seek in real time while dragging"""
        if self.seeking and self.duration_ms > 0:
            position_ms = int((value / 100.0) * self.duration_ms)
            self.update_time_display(position_ms, self.duration_ms)
            
            # Real-time seeking while dragging (throttled for performance)
            self.pending_seek_position = position_ms
            self.seek_timer.start(50)  # Throttle to max 20 seeks per second
            
    def perform_delayed_seek(self):
        """Perform the actual seek (throttled)"""
        if self.seeking:
            print(f"Real-time seeking to: {self.pending_seek_position}ms")  # Debug
            self.seek_requested.emit(self.pending_seek_position)
    
    def update_position(self, position_ms):
        """Update position from video player"""
        self.position_ms = position_ms
        
        # Only update slider if user is not currently dragging it
        if self.duration_ms > 0 and not self.seeking:
            progress = (position_ms / self.duration_ms) * 100
            self.progress_slider.setValue(int(progress))
        
        # Always update time display
        self.update_time_display(position_ms, self.duration_ms)
        
    def update_duration(self, duration_ms):
        """Update duration from video player"""
        self.duration_ms = duration_ms
        self.update_time_display(self.position_ms, duration_ms)
        
    def update_time_display(self, position_ms, duration_ms):
        """Update time display"""
        current_time = self.format_time(position_ms)
        total_time = self.format_time(duration_ms)
        self.time_label.setText(f"{current_time} / {total_time}")
        
    def format_time(self, ms):
        """Format time in mm:ss format"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
        
    def reset_controls(self):
        """Reset controls to initial state"""
        self.is_playing = False
        self.play_btn.setText("▶")
        self.progress_slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")
        self.duration_ms = 0
        self.position_ms = 0
        self.update_export_button(False)  # Disable export button when no video

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.video_player = None
        self.frame_manager = None
        self.current_video_path = None
        self.setup_video_engine()
        self.setup_ui()
        self.connect_signals()
        
    def setup_video_engine(self):
        """Initialize video player engine"""
        self.video_player = VideoPlayerEngine()
        self.frame_manager = FrameManager()
        
    def setup_ui(self):
        self.setWindowTitle("VideoPlayerPro")
        # Set better default size
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        
        # Center the window on screen
        self.center_window()
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: white;
                border: none;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Video container (like original)
        self.video_container = QWidget()
        self.video_container.setStyleSheet("background-color: #000000;")
        container_layout = QVBoxLayout(self.video_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Video widget
        self.video_widget = VideoWidget()
        container_layout.addWidget(self.video_widget)
        
        # Connect video widget signals
        self.video_widget.file_dropped.connect(self.on_file_dropped)
        print("Video widget signals connected")  # Debug
        
        # Controls overlay - positioned as overlay (like original)
        self.controls = ControlsWidget()
        self.controls.setParent(self.video_container)
        
        layout.addWidget(self.video_container)
        
        # Setup menu bar
        self.setup_menubar()
        
        # Position controls after UI is set up
        QTimer.singleShot(100, self.position_controls)
        
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        
    def position_controls(self):
        """Position controls at bottom of video container"""
        if hasattr(self, 'controls') and hasattr(self, 'video_container'):
            # Get container size
            container_size = self.video_container.size()
            
            # Set controls to full width and height of container
            self.controls.resize(container_size)
            
            # Position at (0,0) - controls will position themselves at bottom
            self.controls.move(0, 0)
        
    def setup_menubar(self):
        """Setup modern menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = file_menu.addAction("Open Video...")
        open_action.triggered.connect(self.open_file)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
    def connect_signals(self):
        """Connect all signals"""
        # Video player signals
        self.video_player.frame_ready.connect(self.on_frame_ready)
        self.video_player.position_changed.connect(self.controls.update_position)
        self.video_player.duration_changed.connect(self.controls.update_duration)
        self.video_player.playback_finished.connect(self.on_playback_finished)
        self.video_player.error_occurred.connect(self.on_error)
        
        # Controls signals
        self.controls.play_pause_clicked.connect(self.toggle_play_pause)
        self.controls.stop_clicked.connect(self.stop_video)
        self.controls.seek_requested.connect(self.video_player.seek_to_position)
        self.controls.frame_step_requested.connect(self.on_frame_step)
        self.controls.export_gif_requested.connect(self.open_gif_export_dialog)
        self.controls.volume_changed.connect(self.video_player.set_volume)  # Connect volume control
        
        # Debug: Print when signals are connected
        print("All signals connected successfully")
        
    def on_frame_ready(self, cv_frame):
        """Handle new frame from video player"""
        pixmap = self.frame_manager.convert_cv_to_qt(cv_frame)
        self.video_widget.display_frame(pixmap)
        
    def on_playback_finished(self):
        """Handle playback finished"""
        self.controls.reset_controls()
        
    def on_error(self, error_message):
        """Handle video player errors"""
        QMessageBox.critical(self, "Video Player Error", error_message)
        
    def on_frame_step(self, direction):
        """Handle frame stepping"""
        print(f"Frame step requested: {direction}")  # Debug
        if direction == 1:
            print("Calling next_frame()")  # Debug
            self.video_player.next_frame()
        elif direction == -1:
            print("Calling previous_frame()")  # Debug
            self.video_player.previous_frame()
            
    def on_file_dropped(self, file_path):
        """Handle file dropped on video widget"""
        print(f"File dropped signal received: {file_path}")  # Debug
        if file_path:  # File was dropped
            self.load_video(file_path)
        else:  # Video widget was clicked
            self.open_file()
            
    def open_gif_export_dialog(self):
        """Open the GIF export dialog"""
        print("Opening GIF export dialog")  # Debug
        
        if not self.current_video_path:
            QMessageBox.warning(self, "No Video", "Please load a video first.")
            return
            
        if not self.video_player.video_capture:
            QMessageBox.warning(self, "No Video", "No video is currently loaded.")
            return
            
        # Get current video info
        duration_ms = self.video_player.get_duration_ms()
        current_position_ms = self.video_player.get_current_time_ms()
        
        # Open export dialog
        dialog = GifExportDialog(
            parent=self,
            video_path=self.current_video_path,
            duration_ms=duration_ms,
            current_position_ms=current_position_ms
        )
        
        # Show dialog
        dialog.exec()
        
    def load_video(self, video_path):
        """Load a video file"""
        print(f"Loading video: {video_path}")  # Debug
        if self.video_player.load_video(video_path):
            self.current_video_path = video_path
            self.setWindowTitle(f"VideoPlayerPro - {os.path.basename(video_path)}")
            print(f"Video loaded successfully: {video_path}")
            
            # Enable export button
            self.controls.update_export_button(True)
            
            # Show video info
            info = self.video_player.get_video_info()
            print(f"Video Info: {info}")
        else:
            print(f"Failed to load video: {video_path}")
            self.controls.update_export_button(False)
        
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        # Reposition controls when window is resized
        QTimer.singleShot(10, self.position_controls)
        
    def open_file(self):
        """Open video file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.gif *.wmv *.flv *.webm);;All Files (*)"
        )
        
        if file_path:
            self.load_video(file_path)
            
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if not self.current_video_path:
            self.open_file()
            return
            
        if self.controls.is_playing:
            self.video_player.play()
        else:
            self.video_player.pause()
            
    def stop_video(self):
        """Stop video playback"""
        if self.video_player:
            self.video_player.stop()
            
    def closeEvent(self, event):
        """Handle application close"""
        if self.video_player:
            self.video_player.cleanup()
        event.accept()

# Test the main window
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())