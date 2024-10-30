from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QFontMetrics, QIcon
import sys
import os
import yt_dlp
import re

# Dark theme and uhh blue buttons
modern_style = '''
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', Arial;
    font-size: 10pt;
}

QPushButton {
    background-color: #2d2d2d;
    border: none;
    border-radius: 5px;
    padding: 8px 15px;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #3d3d3d;
}

QPushButton:pressed {
    background-color: #404040;
}

QPushButton:checked {
    background-color: #0078d4;
    color: white;
}

QPushButton#CloseButton {
    background-color: transparent;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#CloseButton:hover {
    background-color: #c42b1c;
}

QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 5px;
    padding: 5px;
    color: white;
}

QLineEdit:focus {
    border: 1px solid #0078d4;
}

QLabel {
    color: #ffffff;
}

#TitleBar {
    background-color: #2d2d2d;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}

#MainWindow {
    border-radius: 10px;
    border: 1px solid #3d3d3d;
}
'''

class VideoProcessingThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, video_url, download_format):
        super().__init__()
        self.video_url = video_url
        self.download_format = download_format

    def run(self):
        exe_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        download_directory = os.path.join(exe_path, "YTDLE")
        os.makedirs(download_directory, exist_ok=True)

        if self.download_format == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '320',
                    },
                    {
                        'key': 'EmbedThumbnail',
                    },
                ],
                'writethumbnail': True,
                'outtmpl': os.path.join(download_directory, sanitize_filename('%(title)s.%(ext)s')),
            }
        else:
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    },
                ],
                'outtmpl': os.path.join(download_directory, sanitize_filename('%(title)s.%(ext)s')),
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([self.video_url])
            except yt_dlp.utils.DownloadError:
                self.finished.emit("Error: Could not download the video or playlist.")
                return

        self.finished.emit("Download completed successfully!")

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

class DraggableTitleBar(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mouse_pressed = False
        self.mouse_position = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = True
            self.mouse_position = event.globalPos() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.mouse_pressed:
            self.window().move(event.globalPos() - self.mouse_position)

    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False

class CustomTitleBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TitleBar")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        self.title_label = DraggableTitleBar("YouTube Downloader")
        self.title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.minimize_button = QPushButton("−")
        self.minimize_button.setObjectName("CloseButton")
        self.minimize_button.clicked.connect(self.window().showMinimized)
        layout.addWidget(self.minimize_button)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("CloseButton")
        # Change this line to use QApplication.quit()
        self.close_button.clicked.connect(QApplication.quit)
        layout.addWidget(self.close_button)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setObjectName("MainWindow")
        self.setMinimumWidth(450)
        self.setMinimumHeight(200)

        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 10, 20, 20)
        
        # Add title bar
        title_bar = CustomTitleBar()
        main_layout.addWidget(title_bar)

        # URL input section
        url_layout = QVBoxLayout()
        url_label = QLabel("Enter YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://youtube.com/...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)

        # Format sel
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        self.mp3_button = QPushButton("MP3")
        self.mp4_button = QPushButton("MP4")
        
        self.mp3_button.setCheckable(True)
        self.mp4_button.setCheckable(True)
        self.mp3_button.setChecked(True)
        
        self.mp3_button.clicked.connect(lambda: self.mp4_button.setChecked(False))
        self.mp4_button.clicked.connect(lambda: self.mp3_button.setChecked(False))
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.mp3_button)
        format_layout.addWidget(self.mp4_button)
        format_layout.addStretch()
        main_layout.addLayout(format_layout)

        # Download button
        self.download_button = QPushButton("Download")
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self.process_video)
        main_layout.addWidget(self.download_button)

        # Status labl
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()
        self.setCentralWidget(main_widget)

    def process_video(self):
        video_url = self.url_input.text()
        if not video_url:
            self.status_label.setText("Please enter a valid URL")
            return

        download_format = 'mp3' if self.mp3_button.isChecked() else 'mp4'
        self.status_label.setText("Downloading... Please wait.")
        self.download_button.setEnabled(False)
        
        self.thread = VideoProcessingThread(video_url, download_format)
        self.thread.finished.connect(self.on_processing_finished)
        self.thread.start()

    def on_processing_finished(self, message):
        self.status_label.setText(message)
        self.download_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(modern_style)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
