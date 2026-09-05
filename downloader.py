import yt_dlp
import os
import sys
import threading
from typing import Dict, List, Tuple, Optional, Callable


def get_ffmpeg_location() -> Optional[str]:
    """Return FFmpeg directory for packaged or development mode."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled_bin = os.path.join(sys._MEIPASS, 'bin')
        if os.path.exists(os.path.join(bundled_bin, 'ffmpeg.exe')):
            return bundled_bin

    local_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')
    if os.path.exists(os.path.join(local_bin, 'ffmpeg.exe')):
        return local_bin

    return None


class YouTubeDownloader:
    """Клас для завантаження відео з YouTube"""

    def __init__(self):
        self.progress_callback = None
        self.status_callback = None
        self.error_callback = None
        self.complete_callback = None
        self.is_downloading = False
        self.current_download = None

    def set_callbacks(self, progress_callback: Optional[Callable] = None,
                      status_callback: Optional[Callable] = None,
                      error_callback: Optional[Callable] = None,
                      complete_callback: Optional[Callable] = None):
        """Установка callback функцій для відстеження прогресу"""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.error_callback = error_callback
        self.complete_callback = complete_callback

    def get_video_info(self, url: str) -> Tuple[Optional[str], List[int]]:
        """
        Отримання інформації про відео та доступних якостей

        Returns:
            Tuple[title, list_of_qualities]
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            ffmpeg_location = get_ffmpeg_location()
            if ffmpeg_location:
                ydl_opts['ffmpeg_location'] = ffmpeg_location

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')

                formats = info.get('formats', [])
                qualities = set()

                for f in formats:
                    height = f.get('height')
                    vcodec = f.get('vcodec')

                    if height and height in [480, 720, 1080, 144, 240, 360, 2160]:
                        if vcodec != 'none':
                            qualities.add(height)

                return title, sorted(list(qualities))

        except Exception as e:
            if self.error_callback:
                self.error_callback(f"Помилка отримання інформації: {str(e)}")
            return None, []

    def download_video(self, url: str, quality: int, output_path: str = '.',
                       filename_template: str = '%(title)s.%(ext)s'):
        """
        Завантаження відео з обраною якістю

        Args:
            url: Посилання на відео
            quality: Бажана якість (480, 720, 1080 і т.д.)
            output_path: Шлях для збереження
            filename_template: Шаблон імені файлу
        """
        if self.is_downloading:
            if self.error_callback:
                self.error_callback("Завантаження вже виконується")
            return False

        def progress_hook(d):
            """Хук для відстеження прогресу"""
            if d['status'] == 'downloading':
                if self.progress_callback:
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)

                    if total > 0:
                        percent = (downloaded / total) * 100
                        speed = d.get('speed', 0)
                        eta = d.get('eta', 0)

                        self.progress_callback(percent, speed, eta)

            elif d['status'] == 'finished':
                if self.status_callback:
                    self.status_callback("Обробка відео...")

            elif d['status'] == 'error':
                if self.error_callback:
                    self.error_callback("Помилка при завантаженні")

        try:
            self.is_downloading = True

            if not os.path.exists(output_path):
                os.makedirs(output_path)

            ydl_opts = {
                'format': self._get_format_selector(quality),
                'outtmpl': os.path.join(output_path, filename_template),
                'merge_output_format': 'mp4',
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': False,
                'ignoreerrors': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }

            ffmpeg_location = get_ffmpeg_location()
            if ffmpeg_location:
                ydl_opts['ffmpeg_location'] = ffmpeg_location

            if self.status_callback:
                self.status_callback(f"Починаю завантаження в якості {quality}p...")

            download_thread = threading.Thread(target=self._download_thread,
                                               args=(url, ydl_opts))
            download_thread.daemon = True
            download_thread.start()

            return True

        except Exception as e:
            self.is_downloading = False
            if self.error_callback:
                self.error_callback(f"Помилка: {str(e)}")
            return False

    def _download_thread(self, url: str, ydl_opts: Dict):
        """Потік для завантаження"""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.is_downloading = False
            if self.complete_callback:
                self.complete_callback()

        except Exception as e:
            self.is_downloading = False
            if self.error_callback:
                self.error_callback(f"Помилка при завантаженні: {str(e)}")

    def _get_format_selector(self, quality: int) -> str:
        """
        Повертає селектор формату для yt-dlp

        Args:
            quality: Бажана якість відео
        """
        return f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'

    def cancel_download(self):
        """Скасування поточного завантаження"""
        self.is_downloading = False
        if self.status_callback:
            self.status_callback("Завантаження скасовано")