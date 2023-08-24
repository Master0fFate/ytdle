from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QWidget, QLabel, QRadioButton
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QFontMetrics
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

QPushButton#CloseButton {
    background-color: #505050;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 5px;
    min-width: 30px;
}

QPushButton#CloseButton:hover {
    background-color: #707070;
}

QPushButton#CloseButton:pressed {
    background-color: #303030;
}

QLabel {
    color: #ffffff;
}

QRadioButton {
    color: #ffffff;
    spacing: 5px;
}

QRadioButton::indicator {
    border: 1px solid #3a3a3a;
    border-radius: 7px;
    width: 16px;
    height: 16px;
}

QRadioButton::indicator:checked {
    background-color: #505050;
}

QRadioButton::indicator:hover {
    border-color: #707070;
}

QRadioButton::indicator:checked:hover {
    background-color: #707070;
}
QPushButton:checked {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 5px;
    min-width: 80px;
}

QPushButton:checked:hover {
    background-color: #e0e0e0;
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

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = DraggableTitleBar("YouTube Downloader A/V | by github.com/Master0fFate")
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.close_button = QPushButton("X")
        self.close_button.setObjectName("CloseButton")
        button_text_width = QFontMetrics(self.close_button.font()).width(self.close_button.text())
        button_text_height = QFontMetrics(self.close_button.font()).height()
        self.close_button.setFixedSize(button_text_width + 1, button_text_height + 10)  # Set the button size dynamically
        self.close_button.clicked.connect(self.on_close_button_clicked)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def on_close_button_clicked(self):
        self.window().close()

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

        self.finished.emit("SUCCESS")


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("YouTube Downloader A/V | by github.com/Master0fFate")
        self.setGeometry(100, 100, 400, 150)
        title_text = "YouTube Downloader A/V | by github.com/Master0fFate"
        title_width = QFontMetrics(self.font()).width(title_text)
        window_width = max(400, title_width + 100)  # Add some padding to the width
        self.setGeometry(100, 100, window_width, 150)

        self.setMenuWidget(CustomTitleBar())

        layout = QVBoxLayout()

        self.url_label = QLabel("Enter the YouTube video/playlist URL:")
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)


        format_buttons_layout = QHBoxLayout()

        self.mp3_button = QPushButton("MP3")
        self.mp3_button.setCheckable(True)
        self.mp3_button.setChecked(True)
        self.mp3_button.clicked.connect(self.select_mp3)
        self.mp3_button.setFixedSize(50, 25)  # Set the button size
        format_buttons_layout.addWidget(self.mp3_button)

        self.mp4_button = QPushButton("MP4")
        self.mp4_button.setCheckable(True)
        self.mp4_button.clicked.connect(self.select_mp4)
        self.mp4_button.setFixedSize(50, 25)  # Set the button size
        format_buttons_layout.addWidget(self.mp4_button)

        layout.addLayout(format_buttons_layout)
        ###################################################
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.process_video)
        layout.addWidget(self.submit_button)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


    def select_mp3(self):
        self.mp3_button.setChecked(True)
        self.mp4_button.setChecked(False)

    def select_mp4(self):
        self.mp3_button.setChecked(False)
        self.mp4_button.setChecked(True)

    def process_video(self):
        video_url = self.url_input.text()
        #download_format = 'mp3' if self.mp3_radio.isChecked() else 'mp4'
        download_format = 'mp3' if self.mp3_button.isChecked() else 'mp4'
        self.status_label.setText("Processing... Please wait until everything is downloaded.")
        self.thread = VideoProcessingThread(video_url, download_format)
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
