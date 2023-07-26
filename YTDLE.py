from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLineEdit, QPushButton, QWidget, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
import sys
import os
import subprocess
import yt_dlp
import re

dark_theme_style = '''
QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
}

QPushButton {
    background-color: #505050;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 5px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #707070;
}

QPushButton:pressed {
    background-color: #303030;
}

QLabel {
    color: #ffffff;
}
'''

class DraggableTitleBar(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mouse_pressed = False
        self.mouse_position = QPoint()

    def mousePressEvent(self, event):
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

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = DraggableTitleBar("YouTube Thumbnail Embedder & Downloader by github.com/Master0fFate")
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.close_button = QPushButton("X")
        self.close_button.clicked.connect(self.on_close_button_clicked)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def on_close_button_clicked(self):
        self.window().close()

class VideoProcessingThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, video_url):
        super().__init__()
        self.video_url = video_url

    def run(self):
        # Download the audio file and embed the thumbnail
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
            'outtmpl': sanitize_filename('%(title)s.%(ext)s'),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([self.video_url])
            except yt_dlp.utils.DownloadError:
                self.finished.emit("Error: Could not download the video or playlist.")
                return

        self.finished.emit("SUCCESS")


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("YouTube Download and Thumbnail Embed by github.com/Master0fFate")
        self.setGeometry(100, 100, 400, 150)

        self.setMenuWidget(CustomTitleBar())

        layout = QVBoxLayout()

        self.url_label = QLabel("Enter the YouTube video/playlist URL:")
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.process_video)
        layout.addWidget(self.submit_button)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def process_video(self):
        video_url = self.url_input.text()
        self.status_label.setText("Processing... Please wait until everything is downloaded.")
        self.thread = VideoProcessingThread(video_url)
        self.thread.finished.connect(self.on_processing_finished)
        self.thread.start()

    def on_processing_finished(self, message):
        self.status_label.setText(message)

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_theme_style)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()