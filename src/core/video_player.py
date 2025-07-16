# src/core/video_player.py

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMutex, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QImage, QPixmap
import time
import os

class VideoPlayerEngine(QThread):
    """Core video playback engine using OpenCV for video + QMediaPlayer for audio"""
    
    # Signals
    frame_ready = pyqtSignal(np.ndarray)  # Emit frame data
    position_changed = pyqtSignal(int)    # Current position in ms
    duration_changed = pyqtSignal(int)    # Total duration in ms
    playback_finished = pyqtSignal()      # Video finished playing
    error_occurred = pyqtSignal(str)      # Error messages
    
    def __init__(self):
        super().__init__()
        
        # OpenCV for video (like original)
        self.video_capture = None
        self.is_playing = False
        self.is_paused = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.frame_duration = 1000 / self.fps  # Duration per frame in ms
        self.video_path = None
        self.seek_to_frame = -1
        self.mutex = QMutex()
        
        # QMediaPlayer ONLY for audio
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # Connect audio player signals
        self.media_player.durationChanged.connect(self.on_audio_duration_changed)
        self.media_player.mediaStatusChanged.connect(self.on_audio_status_changed)
        self.media_player.errorOccurred.connect(self.on_audio_error)
        
    def load_video(self, video_path):
        """Load a video file"""
        try:
            if not os.path.exists(video_path):
                self.error_occurred.emit(f"File not found: {video_path}")
                return False
                
            # Release previous video if any
            if self.video_capture:
                self.video_capture.release()
                
            # Open new video with OpenCV (like original)
            self.video_capture = cv2.VideoCapture(video_path)
            
            if not self.video_capture.isOpened():
                self.error_occurred.emit(f"Cannot open video: {video_path}")
                return False
                
            # Get video properties
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            
            if self.fps <= 0:
                self.fps = 30  # Fallback FPS
                
            self.frame_duration = 1000 / self.fps
            duration_ms = int((self.total_frames / self.fps) * 1000)
            
            self.video_path = video_path
            self.current_frame = 0
            
            # Load audio separately
            media_url = QUrl.fromLocalFile(os.path.abspath(video_path))
            self.media_player.setSource(media_url)
            self.audio_output.setVolume(0.7)  # 70% volume
            
            # Emit video properties
            self.duration_changed.emit(duration_ms)
            
            # Load first frame (like original)
            ret, frame = self.video_capture.read()
            if ret:
                self.frame_ready.emit(frame)
                
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Error loading video: {str(e)}")
            return False
    
    def play(self):
        """Start video playback"""
        if self.video_capture and self.video_capture.isOpened():
            self.is_playing = True
            self.is_paused = False
            
            # Start audio
            self.media_player.play()
            
            if not self.isRunning():
                self.start()
    
    def pause(self):
        """Pause video playback"""
        self.is_paused = True
        self.media_player.pause()
        
    def stop(self):
        """Stop video playback"""
        self.is_playing = False
        self.is_paused = False
        self.current_frame = 0
        
        # Stop audio
        self.media_player.stop()
        
        if self.video_capture:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video_capture.read()
            if ret:
                self.frame_ready.emit(frame)
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        self.position_changed.emit(0)
        
    def seek_to_position(self, position_ms):
        """Seek to a specific time position"""
        if not self.video_capture:
            return
            
        print(f"Seeking to position: {position_ms}ms")  # Debug
        
        target_frame = int((position_ms / 1000.0) * self.fps)
        target_frame = max(0, min(target_frame, self.total_frames - 1))
        
        print(f"Target frame: {target_frame}")  # Debug
        
        # Sync audio
        self.media_player.setPosition(position_ms)
        
        # Immediately seek and emit frame (like original)
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        self.current_frame = target_frame
        
        # Read and emit the frame immediately
        ret, frame = self.video_capture.read()
        if ret:
            self.frame_ready.emit(frame)
            print("Frame emitted after seek")  # Debug
        else:
            print("Failed to read frame after seek")  # Debug
            
        # Reset position for next read
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
        # Emit position update
        self.position_changed.emit(self.get_current_time_ms())
        
        # Also set the seek flag for the threaded playback
        self.mutex.lock()
        self.seek_to_frame = target_frame
        self.mutex.unlock()
        
    def seek_to_frame_number(self, frame_number):
        """Seek to specific frame number"""
        if not self.video_capture:
            return
            
        print(f"Seeking to frame: {frame_number}")  # Debug
        
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        
        # Calculate position for audio sync
        position_ms = int((frame_number / self.fps) * 1000)
        
        # Sync audio
        self.media_player.setPosition(position_ms)
        
        # Immediately seek and emit frame (like original)
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self.current_frame = frame_number
        
        # Read and emit the frame immediately
        ret, frame = self.video_capture.read()
        if ret:
            self.frame_ready.emit(frame)
            print("Frame emitted after frame seek")  # Debug
        else:
            print("Failed to read frame after frame seek")  # Debug
            
        # Reset position for next read
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
        # Emit position update
        self.position_changed.emit(self.get_current_time_ms())
        
        # Also set the seek flag for the threaded playback
        self.mutex.lock()
        self.seek_to_frame = frame_number
        self.mutex.unlock()
        
    def next_frame(self):
        """Go to next frame"""
        if self.current_frame < self.total_frames - 1:
            self.seek_to_frame_number(self.current_frame + 1)
            
    def previous_frame(self):
        """Go to previous frame"""
        if self.current_frame > 0:
            self.seek_to_frame_number(self.current_frame - 1)
            
    def set_volume(self, volume):
        """Set audio volume (0-100)"""
        self.audio_output.setVolume(volume / 100.0)
            
    def get_current_time_ms(self):
        """Get current playback time in milliseconds"""
        return int((self.current_frame / self.fps) * 1000)
        
    def get_duration_ms(self):
        """Get total video duration in milliseconds"""
        if self.video_capture:
            return int((self.total_frames / self.fps) * 1000)
        return 0
        
    def get_video_info(self):
        """Get video information dictionary"""
        if not self.video_capture:
            return {}
            
        width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return {
            'width': width,
            'height': height,
            'fps': self.fps,
            'total_frames': self.total_frames,
            'duration_ms': self.get_duration_ms(),
            'current_frame': self.current_frame,
            'path': self.video_path
        }
    
    def run(self):
        """Main playback loop (like original)"""
        last_frame_time = time.time()
        
        while self.is_playing and self.video_capture and self.video_capture.isOpened():
            current_time = time.time()
            
            # Handle seeking
            self.mutex.lock()
            if self.seek_to_frame >= 0:
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, self.seek_to_frame)
                self.current_frame = self.seek_to_frame
                self.seek_to_frame = -1
                last_frame_time = current_time
                
                # Sync audio position
                audio_position_ms = int((self.current_frame / self.fps) * 1000)
                self.media_player.setPosition(audio_position_ms)
            self.mutex.unlock()
            
            # Skip frame timing if paused
            if self.is_paused:
                self.msleep(16)  # Sleep for ~60 FPS
                continue
                
            # Check if it's time for the next frame
            if (current_time - last_frame_time) >= (self.frame_duration / 1000.0):
                ret, frame = self.video_capture.read()
                
                if ret:
                    self.frame_ready.emit(frame)
                    self.current_frame += 1
                    
                    # Emit position
                    position_ms = self.get_current_time_ms()
                    self.position_changed.emit(position_ms)
                    
                    last_frame_time = current_time
                    
                    # Check if we've reached the end
                    if self.current_frame >= self.total_frames:
                        self.playback_finished.emit()
                        self.is_playing = False
                        break
                else:
                    # End of video
                    self.playback_finished.emit()
                    self.is_playing = False
                    break
                    
            # Small sleep to prevent high CPU usage
            self.msleep(1)
    
    # Audio player signal handlers
    def on_audio_duration_changed(self, duration_ms):
        """Handle audio duration changed"""
        # We use video duration, not audio duration
        pass
        
    def on_audio_status_changed(self, status):
        """Handle audio status changes"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Audio ended - stop video too
            if self.is_playing:
                self.playback_finished.emit()
                self.is_playing = False
                
    def on_audio_error(self, error, error_string):
        """Handle audio player errors"""
        print(f"Audio error: {error_string}")  # Just log, don't fail video
    
    def cleanup(self):
        """Clean up resources"""
        self.is_playing = False
        self.wait()  # Wait for thread to finish
        
        self.media_player.stop()
        
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None