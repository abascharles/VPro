# src/core/gif_exporter.py

import cv2
import numpy as np
from PIL import Image, ImageSequence
import os
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal
import time

# Try to import moviepy, but make it optional
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
    print("MoviePy available - will use for better quality GIF export")
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("MoviePy not available - using OpenCV+PIL fallback")

class GifExporter(QThread):
    """Export video segments as GIF files"""
    
    # Signals
    progress_updated = pyqtSignal(int)        # Progress percentage (0-100)
    export_finished = pyqtSignal(str)         # Path to exported GIF
    export_failed = pyqtSignal(str)           # Error message
    
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.output_path = None
        self.start_time = 0
        self.end_time = 0
        self.fps = 10
        self.width = 480
        self.height = 270
        self.quality = 85
        self.cancel_export = False
        
    def setup_export(self, video_path, output_path, start_time, end_time, 
                     fps=10, width=480, height=270, quality=85):
        """Setup export parameters"""
        self.video_path = video_path
        self.output_path = output_path
        self.start_time = start_time  # in seconds
        self.end_time = end_time      # in seconds
        self.fps = fps
        self.width = width
        self.height = height
        self.quality = quality
        self.cancel_export = False
        
    def cancel(self):
        """Cancel the current export"""
        self.cancel_export = True
        
    def run(self):
        """Main export thread"""
        try:
            self.progress_updated.emit(0)
            
            # Method 1: Using moviepy (recommended for better quality) if available
            if MOVIEPY_AVAILABLE and self._export_with_moviepy():
                self.export_finished.emit(self.output_path)
            else:
                # Method 2: Using OpenCV + PIL (always available)
                self._export_with_opencv()
                self.export_finished.emit(self.output_path)
                
        except Exception as e:
            self.export_failed.emit(f"Export failed: {str(e)}")
            
    def _export_with_moviepy(self):
        """Export using moviepy (better quality) - only if available"""
        if not MOVIEPY_AVAILABLE:
            return False
            
        try:
            self.progress_updated.emit(10)
            
            # Load video clip
            clip = VideoFileClip(self.video_path)
            
            # Extract subclip
            subclip = clip.subclip(self.start_time, self.end_time)
            
            self.progress_updated.emit(30)
            
            # Resize if needed
            if self.width and self.height:
                subclip = subclip.resize((self.width, self.height))
                
            self.progress_updated.emit(50)
            
            # Set fps
            subclip = subclip.set_fps(self.fps)
            
            self.progress_updated.emit(70)
            
            # Export as GIF
            subclip.write_gif(
                self.output_path, 
                fps=self.fps,
                opt='OptimizePlus',  # Better optimization
                fuzz=1  # Reduce colors for smaller file size
            )
            
            self.progress_updated.emit(100)
            
            # Clean up
            subclip.close()
            clip.close()
            
            return True
            
        except Exception as e:
            print(f"MoviePy export failed: {e}")
            return False
            
    def _export_with_opencv(self):
        """Fallback export using OpenCV + PIL"""
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise Exception("Cannot open video file")
            
        # Get video properties
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame range
        start_frame = int(self.start_time * original_fps)
        end_frame = int(self.end_time * original_fps)
        
        # Calculate frame step for target fps
        frame_step = max(1, int(original_fps / self.fps))
        
        frames = []
        frame_count = 0
        total_target_frames = (end_frame - start_frame) // frame_step
        
        # Seek to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        while True:
            if self.cancel_export:
                break
                
            ret, frame = cap.read()
            if not ret or cap.get(cv2.CAP_PROP_POS_FRAMES) > end_frame:
                break
                
            # Process every nth frame based on target fps
            if frame_count % frame_step == 0:
                # Resize frame
                frame = cv2.resize(frame, (self.width, self.height))
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
                
                # Update progress
                progress = int((len(frames) / total_target_frames) * 90)
                self.progress_updated.emit(progress)
                
            frame_count += 1
            
        cap.release()
        
        if not frames:
            raise Exception("No frames extracted")
            
        # Save as GIF
        frames[0].save(
            self.output_path,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / self.fps),  # Duration in milliseconds
            loop=0,
            optimize=True,
            quality=self.quality
        )
        
        self.progress_updated.emit(100)
        
    def get_estimated_size(self, video_path, start_time, end_time, fps=10, width=480, height=270):
        """Estimate GIF file size"""
        duration = end_time - start_time
        frame_count = duration * fps
        
        # Rough estimation: each frame ~2KB at 480x270
        bytes_per_frame = (width * height * 3) // 100  # Very rough estimate
        estimated_size = frame_count * bytes_per_frame
        
        return estimated_size
        
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"