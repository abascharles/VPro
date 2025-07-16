# VideoPlayerPro

An advanced video player application with frame-by-frame navigation, timeline preview, and GIF export capabilities.

## Features

- **Frame-by-Frame Navigation**: Navigate through videos frame by frame with precision
- **Timeline with Thumbnail Preview**: Interactive timeline showing video progress with thumbnail previews
- **GIF Export**: Export video segments as optimized GIF files
- **Drag & Drop Support**: Easy file loading with drag and drop functionality
- **Custom Video Controls**: Professional playback controls with volume adjustment
- **Multiple Video Formats**: Support for MP4, AVI, MOV, MKV, and more
- **Optimized Performance**: Efficient video processing and playback

## Requirements

- Python 3.7 or higher
- PyQt5
- OpenCV
- Pillow (PIL)
- NumPy

## Installation

1. Clone the repository:

```bash
git clone https://github.com/videoplayer/VideoPlayerPro.git
cd VideoPlayerPro
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python main.py
```

## Building from Source

To build the application for distribution:

```bash
python setup.py build
```

To create a distributable package:

```bash
python setup.py sdist bdist_wheel
```

## Usage

### Basic Usage

1. Launch the application by running `python main.py`
2. Open a video file using File → Open Video... or drag and drop a video file
3. Use the playback controls to play, pause, or stop the video
4. Use the timeline to navigate through the video
5. Use arrow keys for frame-by-frame navigation

### Frame-by-Frame Navigation

- **Right Arrow**: Step forward one frame
- **Left Arrow**: Step backward one frame
- **Space**: Toggle play/pause

### GIF Export

1. Load a video file
2. Go to File → Export GIF...
3. Set the start and end time for the segment
4. Configure export settings (size, frame rate, quality)
5. Choose output location and click Export

### Keyboard Shortcuts

- **Ctrl+O**: Open video file
- **Ctrl+E**: Export GIF
- **Ctrl+Q**: Quit application
- **Space**: Play/Pause
- **Left Arrow**: Previous frame
- **Right Arrow**: Next frame

## Project Structure

```
VideoPlayerPro/
├── main.py                     # Application entry point
├── requirements.txt            # Dependencies
├── setup.py                   # Installation script
├── README.md                  # Documentation
├── assets/                    # Icons, images, styles
│   ├── icons/
│   └── styles/
├── src/                       # Source code
│   ├── __init__.py
│   ├── app.py                 # Main application class
│   ├── gui/                   # GUI components
│   │   ├── __init__.py
│   │   ├── main_window.py     # Main player window
│   │   ├── video_widget.py    # Custom video display widget
│   │   ├── controls.py        # Playback controls
│   │   ├── timeline.py        # Progress bar with thumbnail preview
│   │   └── export_dialog.py   # GIF export dialog
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── video_player.py    # Video playback engine
│   │   ├── frame_manager.py   # Frame-by-frame navigation
│   │   └── gif_exporter.py    # GIF creation and export
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── file_handler.py    # File operations and drag & drop
│       └── helpers.py         # Helper functions
├── tests/                     # Unit tests
├── build/                     # Build artifacts (auto-generated)
└── dist/                      # Distribution files (auto-generated)
```

## Development

### Setting up Development Environment

1. Clone the repository
2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:

```bash
pip install -r requirements.txt
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
flake8 src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on the GitHub repository or contact support@videoplayer.pro.

## Changelog

### Version 1.0.0

- Initial release
- Frame-by-frame navigation
- Timeline with thumbnail preview
- GIF export functionality
- Drag & drop support
- Multiple video format support

## Acknowledgments

- Built with PyQt5 for the GUI framework
- OpenCV for video processing
- Pillow for image manipulation
- NumPy for numerical operations
