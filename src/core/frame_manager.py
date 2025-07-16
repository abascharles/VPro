# src/core/frame_manager.py

import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

class FrameManager(QObject):
    """Manages video frames and conversions"""
    
    frame_converted = pyqtSignal(QPixmap)
    
    def __init__(self):
        super().__init__()
        
    def convert_cv_to_qt(self, cv_frame):
        """Convert OpenCV frame to Qt QPixmap"""
        try:
            # Convert from BGR to RGB
            rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
            
            # Get frame dimensions
            height, width, channels = rgb_frame.shape
            bytes_per_line = channels * width
            
            # Create QImage
            qt_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(qt_image)
            
            return pixmap
            
        except Exception as e:
            print(f"Error converting frame: {e}")
            return QPixmap()
    
    def scale_frame_to_fit(self, pixmap, widget_size):
        """Scale frame to fit widget while maintaining aspect ratio"""
        if pixmap.isNull():
            return pixmap
            
        # Scale to fit widget size while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            widget_size,
            aspectRatioMode=1,  # Qt.AspectRatioMode.KeepAspectRatio
            transformMode=1     # Qt.TransformationMode.SmoothTransformation
        )
        
        return scaled_pixmap
        
    def extract_frame_at_position(self, video_path, position_ms):
        """Extract a single frame at specific position for thumbnails"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            target_frame = int((position_ms / 1000.0) * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            
            cap.release()
            
            if ret:
                return self.convert_cv_to_qt(frame)
            return None
            
        except Exception as e:
            print(f"Error extracting frame: {e}")
            return None