# src/core/__init__.py
"""Core functionality for VideoPlayerPro"""

from .video_player import VideoPlayerEngine
from .frame_manager import FrameManager
from .gif_exporter import GifExporter

__all__ = ['VideoPlayerEngine', 'FrameManager', 'GifExporter']