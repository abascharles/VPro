# src/gui/main_window.py - Final version with timeline markers and fixes

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QSlider, QFrame, QSizePolicy,
                             QApplication, QFileDialog, QGraphicsDropShadowEffect,
                             QMessageBox, QDialog)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QPen, QBrush

# Import our video engine
from src.core.video_player import VideoPlayerEngine
from src.core.frame_manager import FrameManager
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

class ClickableSlider(QSlider):
    """Enhanced slider with click-to-seek and smooth real-time seeking"""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal):
        super().__init__(orientation)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 2px solid #ffffff;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #106ebe;
                width: 22px;
                height: 22px;
                border-radius: 11px;
                margin: -8px 0;
            }
            QSlider::sub-page:horizontal {
                background: #0078d4;
                border-radius: 3px;
            }
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse press - allow clicking anywhere on slider"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get the slider's usable width (excluding handle margins)
            handle_width = 18  # Handle width from stylesheet
            usable_width = self.width() - handle_width
            
            # Calculate click position relative to usable area
            click_pos = event.position().x() - (handle_width / 2)
            click_pos = max(0, min(usable_width, click_pos))  # Clamp to usable area
            
            if usable_width > 0:
                # Calculate percentage based on usable area
                percentage = click_pos / usable_width
                new_value = int(self.minimum() + percentage * (self.maximum() - self.minimum()))
                new_value = max(self.minimum(), min(self.maximum(), new_value))
                
                print(f"Slider clicked: pos={click_pos:.1f}, width={usable_width}, percentage={percentage:.3f}, value={new_value}")  # Debug
                
                # Set the new value (this will trigger valueChanged signal)
                self.setValue(new_value)
                
        # Call parent to handle normal slider behavior
        super().mousePressEvent(event)

class TimelineSlider(ClickableSlider):
    """Timeline slider with visual markers for GIF start/end points"""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal):
        super().__init__(orientation)
        self.gif_start_pos = 0  # Position 0-1000 for start marker
        self.gif_end_pos = 100   # Position 0-1000 for end marker
        self.show_markers = False
        self.setMinimumHeight(20)  # Slightly taller for markers
        
    def set_gif_markers(self, start_pos, end_pos, show=True):
        """Set GIF start/end marker positions (0-1000 range)"""
        self.gif_start_pos = start_pos
        self.gif_end_pos = end_pos
        self.show_markers = show
        self.update()  # Trigger repaint
        
    def paintEvent(self, event):
        """Custom paint to draw markers"""
        # Draw the normal slider first
        super().paintEvent(event)
        
        if not self.show_markers:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate marker positions
        slider_width = self.width()
        handle_width = 18
        usable_width = slider_width - handle_width
        
        start_x = (handle_width / 2) + (self.gif_start_pos / 1000.0) * usable_width
        end_x = (handle_width / 2) + (self.gif_end_pos / 1000.0) * usable_width
        
        # Draw start marker (green)
        painter.setPen(QPen(QColor(0, 255, 0), 3))
        painter.setBrush(QBrush(QColor(0, 255, 0, 100)))
        painter.drawRect(int(start_x - 2), 2, 4, self.height() - 4)
        
        # Draw start point label
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(int(start_x - 25), 0, 50, 15, Qt.AlignmentFlag.AlignCenter, "START GIF")
        
        # Draw end marker (orange)
        painter.setPen(QPen(QColor(255, 100, 0), 3))
        painter.setBrush(QBrush(QColor(255, 100, 0, 100)))
        painter.drawRect(int(end_x - 2), 2, 4, self.height() - 4)
        
        # Draw end point label
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(int(end_x - 20), 0, 40, 15, Qt.AlignmentFlag.AlignCenter, "END GIF")
        
        # Draw range highlight between markers
        if end_x > start_x:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 165, 0, 30)))  # Orange with transparency
            painter.drawRect(int(start_x), 6, int(end_x - start_x), 8)

class ControlsWidget(QWidget):
    """Controls widget with improved timeline handling"""
    
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
        self.is_seeking = False  # Track if user is actively seeking
        self.seek_timer = QTimer()  # Timer for throttled seeking
        self.seek_timer.setSingleShot(True)
        self.seek_timer.timeout.connect(self.perform_seek)
        self.pending_seek_position = 0
        self.last_seek_time = 0  # Track when we last sent a seek request
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
        
        # Progress slider - use the new timeline slider with markers
        self.progress_slider = TimelineSlider()
        self.progress_slider.setMaximum(1000)  # Higher resolution for smoother seeking
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
        
        self.volume_slider = ClickableSlider()  # Use clickable slider for volume too
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
        """Toggle play/pause state - communicate with main window only"""
        print("Play button clicked")  # Debug
        
        # Don't change state here - let the main window handle it
        # Just emit the signal and let main window decide the action
        print(f"Current controls state before signal: {self.is_playing}")  # Debug
        self.play_pause_clicked.emit()
        
    def on_stop_clicked(self):
        """Handle stop button click"""
        print("Stop button clicked")  # Debug
        self.is_playing = False
        self.play_btn.setText("▶")
        self.stop_clicked.emit()
        
    def on_frame_step_clicked(self, direction):
        """Handle frame step button clicks"""
        print(f"Frame step button clicked: {direction}")  # Debug
        # Use the same signal as keyboard for consistency
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
        """Handle when user starts seeking"""
        print("User started seeking")  # Debug
        self.is_seeking = True
        
    def on_slider_released(self):
        """Handle when user finishes seeking"""
        print("User finished seeking")  # Debug
        self.is_seeking = False
        
        # Stop the timer and perform final seek
        self.seek_timer.stop()
        
        # Perform final precise seek
        if self.duration_ms > 0:
            final_position_ms = int((self.progress_slider.value() / 1000.0) * self.duration_ms)
            print(f"Final seek to: {final_position_ms}ms")  # Debug
            self.seek_requested.emit(final_position_ms)
            
    def on_slider_value_changed(self, value):
        """Handle slider value changes with improved throttling and crash protection"""
        if self.duration_ms > 0:
            position_ms = int((value / 1000.0) * self.duration_ms)
            
            # Always update time display immediately for responsive UI
            self.update_time_display(position_ms, self.duration_ms)
            
            # If user is seeking, throttle the actual video seeks
            if self.is_seeking:
                import time
                current_time = time.time()
                
                # Store the pending seek position
                self.pending_seek_position = position_ms
                
                # More aggressive throttling to prevent crashes
                if current_time - self.last_seek_time > 0.15:  # 150ms throttle (increased)
                    self.seek_timer.stop()  # Stop existing timer
                    self.seek_timer.start(100)  # Start new timer (100ms delay, increased)
                    
    def perform_seek(self):
        """Perform the actual seek operation (throttled with crash protection)"""
        if self.is_seeking:
            import time
            current_time = time.time()
            
            # Extra protection - don't seek if video player is busy
            try:
                # Check if we have a valid position to seek to
                if self.pending_seek_position < 0 or self.pending_seek_position > self.duration_ms:
                    print(f"Invalid seek position: {self.pending_seek_position}ms")  # Debug
                    return
                    
                self.last_seek_time = current_time
                print(f"Throttled seek to: {self.pending_seek_position}ms")  # Debug
                self.seek_requested.emit(self.pending_seek_position)
                
            except Exception as e:
                print(f"Error during seek: {e}")  # Debug
    
    def update_position(self, position_ms):
        """Update position from video player"""
        self.position_ms = position_ms
        
        # Only update slider if user is not currently seeking
        if self.duration_ms > 0 and not self.is_seeking:
            progress = (position_ms / self.duration_ms) * 1000  # Scale to 0-1000
            self.progress_slider.setValue(int(progress))
        
        # Always update time display when not seeking
        if not self.is_seeking:
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
        
    def update_gif_markers(self, start_time_s, end_time_s, duration_s):
        """Update GIF start/end markers on timeline"""
        if duration_s > 0:
            start_pos = int((start_time_s / duration_s) * 1000)
            end_pos = int((end_time_s / duration_s) * 1000)
            self.progress_slider.set_gif_markers(start_pos, end_pos, show=True)
            print(f"Updated GIF markers: start={start_pos}, end={end_pos}")  # Debug
        
    def hide_gif_markers(self):
        """Hide GIF markers on timeline"""
        self.progress_slider.set_gif_markers(0, 0, show=False)
        
    def reset_controls(self):
        """Reset controls to initial state"""
        self.is_playing = False
        self.play_btn.setText("▶")
        self.progress_slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")
        self.duration_ms = 0
        self.position_ms = 0
        self.update_export_button(False)  # Disable export button when no video
        self.hide_gif_markers()  # Hide markers when resetting

class MainWindow(QMainWindow):
    """Main application window with keyboard shortcuts and improved timeline"""
    
    def __init__(self):
        super().__init__()
        self.video_player = None
        self.frame_manager = None
        self.current_video_path = None
        
        # GIF export quick settings (for Ctrl+G shortcut)
        self.gif_start_time = 0.0
        self.gif_end_time = 10.0
        self.last_gif_settings = {
            'fps': 10,
            'width': 480,
            'height': 270,
            'quality': 85
        }
        
        # Track which GIF marker was set most recently
        self.last_marker_set = None  # 'start' or 'end'
        
        self.setup_video_engine()
        self.setup_ui()
        self.connect_signals()
        
        # Enable keyboard shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
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
        
        # Enable keyboard focus for the main window
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()  # Set initial focus
        
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
        
        # Create status bar for feedback
        self.statusBar().showMessage("Ready - Load a video to get started")
        
        # Position controls after UI is set up
        QTimer.singleShot(100, self.position_controls)
        
        # Add periodic health check for video player
        self.health_check_timer = QTimer()
        self.health_check_timer.timeout.connect(self.check_video_player_health)
        self.health_check_timer.start(5000)  # Check every 5 seconds
        
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
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts with crash protection"""
        key = event.key()
        modifiers = event.modifiers()
        
        print(f"Key pressed: {key}, modifiers: {modifiers}, Space key: {Qt.Key.Key_Space}")  # Debug
        
        # Throttle rapid key presses to prevent crashes
        if not hasattr(self, 'last_key_time'):
            self.last_key_time = 0
            
        import time
        current_time = time.time()
        
        # Space for play/pause (make sure it works regardless of focus)
        if key == Qt.Key.Key_Space:
            event.accept()  # Prevent button activation
            print("Space key detected, calling space_play_pause")  # Debug
            self.space_play_pause()  # Use dedicated method for space bar
            return
            
        # Frame navigation with moderate throttling
        elif key == Qt.Key.Key_Comma:  # , for previous frame
            event.accept()
            # Moderate throttling for keyboard responsiveness
            if current_time - self.last_key_time > 0.1:  # 100ms minimum between frame steps
                print("Comma key pressed - previous frame")  # Debug
                self.on_frame_step(-1)
                self.last_key_time = current_time
            else:
                print("Comma key throttled - too fast")  # Debug
            return
            
        elif key == Qt.Key.Key_Period:  # . for next frame
            event.accept()
            # Moderate throttling for keyboard responsiveness
            if current_time - self.last_key_time > 0.1:  # 100ms minimum between frame steps
                print("Period key pressed - next frame")  # Debug
                self.on_frame_step(1)
                self.last_key_time = current_time
            else:
                print("Period key throttled - too fast")  # Debug
            return
            
        # GIF shortcuts
        elif key == Qt.Key.Key_G:
            event.accept()
            print("G key pressed")  # Debug
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                print("Ctrl+G - Quick export")  # Debug
                # Ctrl+G: Quick export GIF
                self.quick_export_gif()
            elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                print("Shift+G - Set end point")  # Debug
                # Shift+G: Set end point
                self.set_gif_end_point()
            else:
                print("G - Set start point")  # Debug
                # G: Set start point
                self.set_gif_start_point()
            return
            
        # Undo/Clear GIF markers
        elif key == Qt.Key.Key_U:
            event.accept()
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                print("Shift+U key pressed - Clear all GIF markers")  # Debug
                self.clear_all_gif_markers()
            else:
                print("U key pressed - Undo latest GIF marker")  # Debug
                self.undo_latest_gif_marker()
            return
            
        # Call parent for other keys
        super().keyPressEvent(event)
        
    def space_play_pause(self):
        """Handle space bar play/pause - works even when no video is playing"""
        print("Space bar pressed for play/pause")  # Debug
        
        if not self.current_video_path:
            print("No video loaded, opening file dialog")  # Debug
            self.open_file()
            return
            
        # Debug video player state
        print(f"Video player state - is_playing: {self.video_player.is_playing}, is_paused: {self.video_player.is_paused}")  # Debug
        print(f"Controls state - is_playing: {self.controls.is_playing}")  # Debug
        
        # Simplified logic - check controls state first, then video player
        if self.controls.is_playing:
            print("Pausing video (controls show playing)")  # Debug
            self.video_player.pause()
            self.controls.is_playing = False
            self.controls.play_btn.setText("▶")
        else:
            print("Playing video (controls show paused)")  # Debug  
            self.video_player.play()
            self.controls.is_playing = True
            self.controls.play_btn.setText("⏸")
        
    def set_gif_start_point(self):
        """Set GIF start point at current position"""
        if self.video_player and self.video_player.video_capture:
            self.gif_start_time = self.video_player.get_current_time_ms() / 1000.0
            print(f"GIF start point set at: {self.gif_start_time:.1f}s")
            
            # Update timeline markers
            duration_s = self.video_player.get_duration_ms() / 1000.0
            self.controls.update_gif_markers(self.gif_start_time, self.gif_end_time, duration_s)
            
            # Show visual feedback
            self.statusBar().showMessage(f"GIF start point set at {self.gif_start_time:.1f}s", 2000)
    def undo_latest_gif_marker(self):
        """Undo the most recently set GIF marker"""
        if not self.video_player or not self.video_player.video_capture:
            self.statusBar().showMessage("No video loaded", 2000)
            return
            
        duration_s = self.video_player.get_duration_ms() / 1000.0
        default_end = min(10.0, duration_s)
        
        # Check if we have any custom markers set (not at default positions)
        has_custom_start = self.gif_start_time != 0.0
        has_custom_end = self.gif_end_time != default_end
        
        if not has_custom_start and not has_custom_end:
            self.statusBar().showMessage("No custom GIF markers to undo", 2000)
            print(f"No custom markers to undo (start={self.gif_start_time:.1f}s, end={self.gif_end_time:.1f}s, default_end={default_end:.1f}s)")  # Debug
            return
        
        print(f"Undoing marker - last_set: {self.last_marker_set}, has_custom_start: {has_custom_start}, has_custom_end: {has_custom_end}")  # Debug
        
        if self.last_marker_set == 'end' and has_custom_end:
            # Reset end marker to default
            self.gif_end_time = default_end
            self.statusBar().showMessage("GIF end marker removed", 2000)
            print(f"Undid end marker - reset to {self.gif_end_time:.1f}s")  # Debug
            
            # If we still have a custom start marker, update last_marker_set
            if has_custom_start:
                self.last_marker_set = 'start'
                self.controls.update_gif_markers(self.gif_start_time, self.gif_end_time, duration_s)
            else:
                # No custom markers left
                self.last_marker_set = None
                self.controls.hide_gif_markers()
                
        elif self.last_marker_set == 'start' and has_custom_start:
            # Reset start marker to default
            self.gif_start_time = 0.0
            self.statusBar().showMessage("GIF start marker removed", 2000)
            print(f"Undid start marker - reset to {self.gif_start_time:.1f}s")  # Debug
            
            # If we still have a custom end marker, update last_marker_set
            if has_custom_end:
                self.last_marker_set = 'end'
                self.controls.update_gif_markers(self.gif_start_time, self.gif_end_time, duration_s)
            else:
                # No custom markers left
                self.last_marker_set = None
                self.controls.hide_gif_markers()
                
        else:
            # Handle case where last_marker_set might be wrong or None
            # Prioritize undoing the most recent non-default marker
            if has_custom_end:
                # Reset end marker
                self.gif_end_time = default_end
                self.statusBar().showMessage("GIF end marker removed", 2000)
                print(f"Undid end marker (fallback) - reset to {self.gif_end_time:.1f}s")  # Debug
                self.last_marker_set = 'start' if has_custom_start else None
                
            elif has_custom_start:
                # Reset start marker  
                self.gif_start_time = 0.0
                self.statusBar().showMessage("GIF start marker removed", 2000)
                print(f"Undid start marker (fallback) - reset to {self.gif_start_time:.1f}s")  # Debug
                self.last_marker_set = None
            
            # Update display
            if self.last_marker_set:
                self.controls.update_gif_markers(self.gif_start_time, self.gif_end_time, duration_s)
            else:
                self.controls.hide_gif_markers()
                
    def clear_all_gif_markers(self):
        """Clear all GIF start and end markers"""
        if self.video_player and self.video_player.video_capture:
            print("Clearing all GIF markers")  # Debug
            
            # Hide markers on timeline
            self.controls.hide_gif_markers()
            
            # Reset GIF times to defaults
            duration_s = self.video_player.get_duration_ms() / 1000.0
            self.gif_start_time = 0.0
            self.gif_end_time = min(10.0, duration_s)
            
            # Reset tracking
            self.last_marker_set = None
            
            # Show visual feedback
            self.statusBar().showMessage("All GIF markers cleared", 2000)
            print(f"All GIF markers cleared - reset to default range: {self.gif_start_time:.1f}s to {self.gif_end_time:.1f}s")  # Debug
        
    def set_gif_end_point(self):
        """Set GIF end point at current position"""
        if self.video_player and self.video_player.video_capture:
            self.gif_end_time = self.video_player.get_current_time_ms() / 1000.0
            print(f"GIF end point set at: {self.gif_end_time:.1f}s")
            
            # Update timeline markers
            duration_s = self.video_player.get_duration_ms() / 1000.0
            self.controls.update_gif_markers(self.gif_start_time, self.gif_end_time, duration_s)
            
            # Show visual feedback
            self.statusBar().showMessage(f"GIF end point set at {self.gif_end_time:.1f}s", 2000)
            print(f"Current GIF range: {self.gif_start_time:.1f}s to {self.gif_end_time:.1f}s")  # Debug
        
    def quick_export_gif(self):
        """Quick export GIF with last used settings"""
        if not self.current_video_path:
            self.statusBar().showMessage("No video loaded", 2000)
            return
            
        if self.gif_end_time <= self.gif_start_time:
            self.statusBar().showMessage("Invalid GIF range - set start and end points first", 3000)
            return
            
        # Get output file path
        suggested_name = f"quick_export_{int(self.gif_start_time)}s-{int(self.gif_end_time)}s.gif"
        output_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Quick Export GIF", 
            suggested_name,
            "GIF Files (*.gif);;All Files (*)"
        )
        
        if not output_path:
            return
            
        # Start quick export with last settings
        from src.core.gif_exporter import GifExporter
        self.quick_gif_exporter = GifExporter()
        self.quick_gif_exporter.setup_export(
            self.current_video_path, 
            output_path, 
            self.gif_start_time, 
            self.gif_end_time,
            self.last_gif_settings['fps'],
            self.last_gif_settings['width'], 
            self.last_gif_settings['height'], 
            self.last_gif_settings['quality']
        )
        
        # Connect signals for feedback
        self.quick_gif_exporter.export_finished.connect(
            lambda path: self.on_quick_export_finished(path)
        )
        self.quick_gif_exporter.export_failed.connect(
            lambda error: self.on_quick_export_failed(error)
        )
        
        self.quick_gif_exporter.start()
        self.statusBar().showMessage("Exporting GIF...", 0)
        
    def on_quick_export_finished(self, path):
        """Handle quick export completion with proper cleanup"""
        self.statusBar().showMessage(f"GIF exported: {os.path.basename(path)}", 5000)
        
        # Hide markers after successful export - ready for next GIF
        self.controls.hide_gif_markers()
        
        # Reset marker tracking
        self.last_marker_set = None
        
        print("GIF markers hidden after export")  # Debug
        
        # IMPORTANT: Reset video player state after export to prevent crashes
        try:
            if self.video_player and self.current_video_path:
                print("Resetting video player after export...")  # Debug
                current_position = self.video_player.get_current_time_ms()
                
                # Stop current playback
                self.video_player.stop()
                
                # Small delay to ensure cleanup
                QTimer.singleShot(100, lambda: self.reload_video_after_export(current_position))
                
        except Exception as e:
            print(f"Error during post-export cleanup: {e}")  # Debug
        
    def reload_video_after_export(self, restore_position=0):
        """Reload video after export to ensure clean state"""
        try:
            if self.current_video_path:
                print(f"Reloading video to restore clean state...")  # Debug
                
                # Stop and cleanup current video player
                self.video_player.cleanup()
                
                # Small delay to ensure cleanup
                QTimer.singleShot(100, lambda: self.perform_video_reload(restore_position))
                    
        except Exception as e:
            print(f"Error reloading video after export: {e}")  # Debug
            
    def perform_video_reload(self, restore_position=0):
        """Actually perform the video reload"""
        try:
            # Reload the video
            if self.video_player.load_video(self.current_video_path):
                # Restore position if specified
                if restore_position > 0:
                    QTimer.singleShot(300, lambda: self.video_player.seek_to_position(restore_position))
                print("Video reloaded successfully after export")  # Debug
                
                # Ensure controls are in correct state
                self.controls.is_playing = False
                self.controls.play_btn.setText("▶")
            else:
                print("Failed to reload video after export")  # Debug
                
        except Exception as e:
            print(f"Error performing video reload: {e}")  # Debug
        
    def on_quick_export_failed(self, error):
        """Handle quick export failure"""
        self.statusBar().showMessage(f"Export failed: {error}", 5000)
        
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
        """Handle new frame from video player with error protection"""
        try:
            if cv_frame is not None and cv_frame.size > 0:
                pixmap = self.frame_manager.convert_cv_to_qt(cv_frame)
                if pixmap and not pixmap.isNull():
                    self.video_widget.display_frame(pixmap)
            else:
                print("Received invalid frame")  # Debug
        except Exception as e:
            print(f"Error handling frame: {e}")  # Debug
            # Don't crash the app, just log the error
        
    def on_playback_finished(self):
        """Handle playback finished"""
        self.controls.reset_controls()
        # Ensure state is properly synced
        self.controls.is_playing = False
        self.controls.play_btn.setText("▶")
        
    def on_error(self, error_message):
        """Handle video player errors"""
        QMessageBox.critical(self, "Video Player Error", error_message)
        
    def on_frame_step(self, direction):
        """Handle frame stepping with enhanced crash protection for rapid clicking"""
        print(f"Frame step requested: {direction}")  # Debug
        
        # Check if video is loaded and healthy
        if not self.video_player or not self.video_player.video_capture:
            print("No video loaded for frame stepping")  # Debug
            return
            
        try:
            # Check if video capture is still valid
            if not self.video_player.video_capture.isOpened():
                print("Video capture not opened - attempting recovery")  # Debug
                self.perform_video_reload()
                return
        except Exception as e:
            print(f"Error checking video capture state: {e}")  # Debug
            return
        
        # Enhanced throttling with rapid click detection
        if not hasattr(self, 'last_frame_step_time'):
            self.last_frame_step_time = 0
            self.frame_step_count = 0
            self.rapid_click_start = 0
            
        import time
        current_time = time.time()
        
        # Track rapid clicking
        if current_time - self.last_frame_step_time < 0.5:  # Less than 500ms apart
            self.frame_step_count += 1
            if self.frame_step_count == 1:
                self.rapid_click_start = current_time
        else:
            # Reset counter if enough time has passed
            self.frame_step_count = 0
            
        # If more than 3 clicks in 2 seconds, apply heavy throttling
        if self.frame_step_count > 3 and (current_time - self.rapid_click_start) < 2.0:
            print(f"Rapid clicking detected ({self.frame_step_count} clicks) - applying heavy throttling")  # Debug
            if current_time - self.last_frame_step_time < 0.3:  # 300ms throttle for rapid clicking
                print("Frame step throttled - rapid clicking protection")  # Debug
                return
        else:
            # Normal throttling
            if current_time - self.last_frame_step_time < 0.1:  # 100ms normal throttle
                print("Frame step throttled - too fast")  # Debug
                return
            
        self.last_frame_step_time = current_time
        
        try:
            # For rapid clicking protection, ensure video is stopped
            if self.frame_step_count > 2:
                # Stop completely for heavy rapid clicking
                if self.video_player.is_playing:
                    self.video_player.stop()
                    print("Stopped video for rapid frame stepping protection")  # Debug
                    QTimer.singleShot(50, lambda: self.execute_protected_frame_step(direction))
                    return
            
            # Normal frame stepping - just pause
            was_playing = self.video_player.is_playing and not self.video_player.is_paused
            if was_playing:
                self.video_player.pause()
                print("Paused video for frame stepping")  # Debug
            
            # Execute frame step directly
            if direction == 1:
                print("Executing next_frame()")  # Debug
                self.video_player.next_frame()
            elif direction == -1:
                print("Executing previous_frame()")  # Debug
                self.video_player.previous_frame()
                
            print("Frame step completed")  # Debug
            
        except Exception as e:
            print(f"Error during frame stepping: {e}")  # Debug
            # Reset rapid click counter on error
            self.frame_step_count = 0
            # Try to recover
            QTimer.singleShot(500, lambda: self.perform_video_reload())
            
    def execute_protected_frame_step(self, direction):
        """Execute frame step with extra protection for rapid clicking"""
        try:
            if direction == 1:
                print("Executing protected next_frame()")  # Debug
                self.video_player.next_frame()
            elif direction == -1:
                print("Executing protected previous_frame()")  # Debug
                self.video_player.previous_frame()
                
            print("Protected frame step completed")  # Debug
            
        except Exception as e:
            print(f"Error in protected frame step: {e}")  # Debug
            # Reset rapid click tracking on error
            self.frame_step_count = 0
            QTimer.singleShot(500, lambda: self.perform_video_reload())
            
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
        
        print(f"Opening export dialog with GIF range: {self.gif_start_time:.1f}s to {self.gif_end_time:.1f}s")  # Debug
        
        # Open export dialog with the correct GIF times
        dialog = ModifiedGifExportDialog(
            parent=self,
            video_path=self.current_video_path,
            duration_ms=duration_ms,
            current_position_ms=current_position_ms,
            gif_start_time=self.gif_start_time,  # Use the actual start time set with G
            gif_end_time=self.gif_end_time       # Use the actual end time set with Shift+G
        )
        
        # Store settings when dialog is accepted
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            # Update last used settings
            self.last_gif_settings.update({
                'fps': dialog.fps_spin.value(),
                'width': dialog.get_export_dimensions()[0],
                'height': dialog.get_export_dimensions()[1],
                'quality': dialog.get_quality_setting()
            })
        
    def load_video(self, video_path):
        """Load a video file with robust error handling"""
        print(f"Loading video: {video_path}")  # Debug
        
        try:
            # Stop health check during loading
            if hasattr(self, 'health_check_timer'):
                self.health_check_timer.stop()
                
            if self.video_player.load_video(video_path):
                self.current_video_path = video_path
                self.setWindowTitle(f"VideoPlayerPro - {os.path.basename(video_path)}")
                print(f"Video loaded successfully: {video_path}")
                
                # Enable export button
                self.controls.update_export_button(True)
                
                # Reset GIF points to reasonable defaults
                self.gif_start_time = 0.0
                duration_s = self.video_player.get_duration_ms() / 1000.0
                self.gif_end_time = min(10.0, duration_s)  # 10 seconds or video length
                
                # Reset marker tracking
                self.last_marker_set = None
                
                # DON'T show markers by default - only show when user presses G
                self.controls.hide_gif_markers()
                
                # Initialize video player state properly
                self.controls.is_playing = False
                self.controls.play_btn.setText("▶")
                
                # Initialize position tracking for health check
                self.last_known_position = 0
                
                # Make sure main window has focus for keyboard shortcuts
                self.setFocus()
                
                # Show video info
                info = self.video_player.get_video_info()
                print(f"Video Info: {info}")
                
                # Restart health check
                if hasattr(self, 'health_check_timer'):
                    self.health_check_timer.start(5000)
                    
            else:
                print(f"Failed to load video: {video_path}")
                self.controls.update_export_button(False)
                if hasattr(self, 'health_check_timer'):
                    self.health_check_timer.start(5000)
                    
        except Exception as e:
            print(f"Error loading video: {e}")  # Debug
            self.controls.update_export_button(False)
            if hasattr(self, 'health_check_timer'):
                self.health_check_timer.start(5000)
        
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
        """Toggle between play and pause - synced with space bar"""
        print("Toggle play/pause called (from button)")  # Debug
        
        if not self.current_video_path:
            self.open_file()
            return
            
        # Use same logic as space_play_pause for consistency
        print(f"Current controls state: {self.controls.is_playing}")  # Debug
        
        if self.controls.is_playing:
            print("Pausing video (button method)")  # Debug
            self.video_player.pause()
            self.controls.is_playing = False
            self.controls.play_btn.setText("▶")
        else:
            print("Playing video (button method)")  # Debug  
            self.video_player.play()
            self.controls.is_playing = True
            self.controls.play_btn.setText("⏸")
            
    def stop_video(self):
        """Stop video playback"""
        if self.video_player:
            self.video_player.stop()
            # Ensure controls state is synced
            self.controls.is_playing = False
            self.controls.play_btn.setText("▶")
            
    def mousePressEvent(self, event):
        """Ensure main window gets focus for keyboard shortcuts"""
        self.setFocus()
        super().mousePressEvent(event)
        
    def check_video_player_health(self):
        """Periodic check to ensure video player is in good state"""
        try:
            if self.video_player and self.current_video_path:
                # Check if video capture is still valid
                if not self.video_player.video_capture or not self.video_player.video_capture.isOpened():
                    print("Video player health check: Video capture is not opened")  # Debug
                    # Try to recover by reloading
                    if hasattr(self, 'last_known_position'):
                        self.perform_video_reload(self.last_known_position)
                    else:
                        self.perform_video_reload()
                else:
                    # Store current position for recovery
                    try:
                        self.last_known_position = self.video_player.get_current_time_ms()
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error in health check: {e}")  # Debug
    
    def focusInEvent(self, event):
        """Handle focus events"""
        print("Main window gained focus")  # Debug
        super().focusInEvent(event)
            
    def closeEvent(self, event):
        """Handle application close"""
        # Stop health check timer
        if hasattr(self, 'health_check_timer'):
            self.health_check_timer.stop()
            
        if self.video_player:
            self.video_player.cleanup()
        event.accept()

class ModifiedGifExportDialog(GifExportDialog):
    """Modified export dialog with fixes for positioning and jump buttons"""
    
    def __init__(self, parent=None, video_path=None, duration_ms=0, current_position_ms=0, gif_start_time=0.0, gif_end_time=10.0):
        # Store the parent window reference first
        self.parent_window = parent
        
        # Store the custom times
        self.custom_start_time = gif_start_time
        self.custom_end_time = gif_end_time
        
        print(f"ModifiedGifExportDialog init: start={gif_start_time}, end={gif_end_time}")  # Debug
        
        # Call parent constructor but we'll override the times after
        super().__init__(parent, video_path, duration_ms, current_position_ms)
        
        # Override the start and end times with the ones set by G/Shift+G
        self.start_time = self.custom_start_time
        self.end_time = self.custom_end_time
        
        print(f"Setting dialog times: start={self.start_time}, end={self.end_time}")  # Debug
        
        # Update sliders to reflect these times (convert to 0.1 second units)
        self.start_slider.setValue(int(self.start_time * 10))
        self.end_slider.setValue(int(self.end_time * 10))
        
        print(f"Slider values set: start={int(self.start_time * 10)}, end={int(self.end_time * 10)}")  # Debug
        
        # Update labels and preview
        self.update_time_labels()
        self.update_preview()
        self.load_frame_previews()
        
        # Connect to parent's export completion to hide markers
        if hasattr(self, 'gif_exporter'):
            self.gif_exporter.export_finished.connect(self.on_export_finished_hide_markers)
    
    def on_export_finished_hide_markers(self, output_path):
        """Handle export completion and hide markers"""
        # Call original handler first
        self.on_export_finished(output_path)
        
        # Hide markers in main window after successful export
        if self.parent_window and hasattr(self.parent_window, 'controls'):
            self.parent_window.controls.hide_gif_markers()
            
            # Reset marker tracking
            self.parent_window.last_marker_set = None
            
            print("GIF markers hidden after dialog export")  # Debug
            
        # Also trigger video reload to prevent crashes
        if self.parent_window:
            QTimer.singleShot(200, lambda: self.parent_window.reload_video_after_export())
    
    def jump_to_start(self):
        """Jump main player to start time - using the actual start time"""
        if self.parent_window and hasattr(self.parent_window, 'video_player'):
            start_ms = int(self.start_time * 1000)
            print(f"Jump to start: {self.start_time}s = {start_ms}ms")  # Debug
            try:
                self.parent_window.video_player.seek_to_position(start_ms)
                print("Jump to start completed")  # Debug
            except Exception as e:
                print(f"Error jumping to start: {e}")  # Debug
            
    def jump_to_end(self):
        """Jump main player to end time - using the actual end time"""
        if self.parent_window and hasattr(self.parent_window, 'video_player'):
            end_ms = int(self.end_time * 1000)
            print(f"Jump to end: {self.end_time}s = {end_ms}ms")  # Debug
            try:
                self.parent_window.video_player.seek_to_position(end_ms)
                print("Jump to end completed")  # Debug
            except Exception as e:
                print(f"Error jumping to end: {e}")  # Debug

# Test the main window
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())