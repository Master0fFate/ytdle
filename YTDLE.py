from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QFontMetrics, QIcon
from PyQt5.QtWidgets import QStyle  # Add this line
import sys
import os
import yt_dlp
import re

modern_style = '''
QWidget {
    background-color: #1a1a1a;
    color: #ffffff;
    font-family: 'Segoe UI', Arial;
    font-size: 10pt;
}

QPushButton {
    background-color: #2d2d2d;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
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

QPushButton#DownloadButton {
    background-color: #0078d4;
    font-weight: bold;
}

QPushButton#DownloadButton:hover {
    background-color: #0086ef;
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
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    padding: 8px;
    color: white;
}

QLineEdit:focus {
    border: 2px solid #0078d4;
}

QComboBox {
    background-color: #2d2d2d;
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    padding: 8px;
    color: white;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid white;
    margin-right: 10px;
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
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, video_url, download_format, quality, download_dir):
        super().__init__()
        self.video_url = video_url
        self.download_format = download_format
        self.quality = quality
        self.download_dir = download_dir

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                total_bytes = d.get('total_bytes')
                downloaded_bytes = d.get('downloaded_bytes')
                
                if total_bytes is None:
                    total_bytes = d.get('total_bytes_estimate', 0)

                if total_bytes and downloaded_bytes:
                    percentage = (downloaded_bytes / total_bytes) * 100
                    self.progress.emit(int(percentage))
                    
                # Emit download speed and ETA
                speed = d.get('speed', 0)
                if speed:
                    speed_mb = speed / 1024 / 1024  # Convert to MB/s
                    eta = d.get('eta', 0)
                    status_text = f"Downloading... {speed_mb:.1f} MB/s"
                    if eta:
                        status_text += f" (ETA: {eta} seconds)"
                    self.status.emit(status_text)

            except Exception as e:
                print(f"Progress calculation error: {str(e)}")
                
        elif d['status'] == 'finished':
            self.status.emit("Processing downloaded file...")

    def run(self):
        try:
            os.makedirs(self.download_dir, exist_ok=True)

            if self.download_format == 'mp3':
                bitrate = self.quality.replace('k', '')
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [
                        {
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': bitrate,
                        },
                        {'key': 'EmbedThumbnail'},
                    ],
                    'writethumbnail': True,
                    'outtmpl': os.path.join(self.download_dir, '%(title).150s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                    'verbose': True,
                    'extract_flat': False,
                }
            else:
                if self.quality == 'Best':
                    fmt = 'bestvideo+bestaudio/best'
                else:
                    height = int(''.join(filter(str.isdigit, self.quality)))
                    fmt = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'

                ydl_opts = {
                    'format': fmt,
                    'merge_output_format': 'mp4',
                    'outtmpl': os.path.join(self.download_dir, '%(title).150s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                    'verbose': True,
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.video_url])
            self.finished.emit("Download completed! Saved to: " + self.download_dir)

        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")


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
        self.title_label = DraggableTitleBar("YTDLE - Media Downloader")
        self.title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.title_label)
        layout.addStretch()
        self.minimize_button = QPushButton("−")
        self.minimize_button.setObjectName("CloseButton")
        self.minimize_button.clicked.connect(self.window().showMinimized)
        layout.addWidget(self.minimize_button)
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("CloseButton")
        self.close_button.clicked.connect(QApplication.quit)
        layout.addWidget(self.close_button)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.set_default_directory()
        self.setup_connections()

    def set_default_directory(self):
        downloads_path = os.path.join(os.path.expanduser("~"), "YTDLE")
        self.dir_input.setText(downloads_path)

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setObjectName("MainWindow")
        self.setMinimumSize(550, 400)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 10, 20, 20)
        
        title_bar = CustomTitleBar()
        main_layout.addWidget(title_bar)

        # Download dir
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        browse_btn = QPushButton()
        browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        browse_btn.clicked.connect(self.choose_directory)
        browse_btn.setToolTip("Choose download directory")
        browse_btn.setFixedWidth(40)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_btn)
        main_layout.addLayout(dir_layout)

        # URL Input
        url_layout = QVBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL (YouTube, Twitter, TikTok, etc.)")
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)

        # Format Select
        format_layout = QHBoxLayout()
        self.format_group = QButtonGroup(self)
        
        self.mp3_btn = QPushButton("MP3")
        self.mp3_btn.setCheckable(True)
        self.mp3_btn.setChecked(True)
        self.format_group.addButton(self.mp3_btn)
        
        self.mp4_btn = QPushButton("MP4")
        self.mp4_btn.setCheckable(True)
        self.format_group.addButton(self.mp4_btn)
        
        # Quality Select
        self.quality_combo = QComboBox()
        
        format_layout.addWidget(QLabel("Format:"))
        format_layout.addWidget(self.mp3_btn)
        format_layout.addWidget(self.mp4_btn)
        format_layout.addWidget(QLabel("Quality:"))
        format_layout.addWidget(self.quality_combo)
        main_layout.addLayout(format_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Download Button
        self.download_btn = QPushButton("Start Download")
        self.download_btn.setObjectName("DownloadButton")
        self.download_btn.setMinimumHeight(40)
        main_layout.addWidget(self.download_btn)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        self.update_quality_options()
        self.setCentralWidget(main_widget)

    def setup_connections(self):
        self.download_btn.clicked.connect(self.validate_and_start_download)
        self.mp3_btn.clicked.connect(self.update_quality_options)
        self.mp4_btn.clicked.connect(self.update_quality_options)

    def choose_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if path:
            self.dir_input.setText(os.path.normpath(path))

    def update_quality_options(self):
        self.quality_combo.clear()
        if self.mp3_btn.isChecked():
            self.quality_combo.addItems(["320k", "192k", "128k"])
        else:
            self.quality_combo.addItems(["Best", "1080p", "720p", "480p"])

    def validate_and_start_download(self):
        url = self.url_input.text().strip()
        download_dir = self.dir_input.text().strip()
            
        if not url:
            self.status_label.setText("Please enter a valid URL")
            return

        if not os.path.isdir(download_dir):
            try:
                os.makedirs(download_dir, exist_ok=True)
            except:
                self.status_label.setText(f"Error: Can't create directory {download_dir}")
                return

        self.download_btn.setEnabled(False)
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setText("Starting download...")
        self.progress_bar.setValue(0)

        self.download_thread = VideoProcessingThread(
            url,
            "mp3" if self.mp3_btn.isChecked() else "mp4",
            self.quality_combo.currentText(),
            download_dir
        )
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.status.connect(self.status_label.setText)  # Add this line
        self.download_thread.finished.connect(self.handle_download_result)
        self.download_thread.start()


    def handle_download_result(self, message):
        self.download_btn.setEnabled(True)
        if "Error" in message:
            self.status_label.setStyleSheet("color: #ff4444;")
            self.progress_bar.setValue(0)
        else:
            self.status_label.setStyleSheet("color: #4CAF50;")
            self.progress_bar.setValue(100)
        self.status_label.setText(message)
        QApplication.beep()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(modern_style)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
