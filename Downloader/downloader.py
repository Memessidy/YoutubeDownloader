import yaml
import yt_dlp
import threading


class YTDownloader:
    def __init__(self, progress_callback=None, finish_callback=None, error_callback=None):
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.error_callback = error_callback
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def load_ydl_opts(self):
        with open('yt-dlp-config.yaml', 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)

        cfg['progress_hooks'] = [self.my_hook]
        return cfg

    def download_from_youtube(self, url):
        ydl_opts = self.load_ydl_opts()

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if self.stop_event.is_set():
                return False
            if self.finish_callback:
                self.finish_callback()
            return True
        except Exception as e:
            if self.stop_event.is_set():
                return False
            if self.error_callback:
                self.error_callback(str(e))
            return False

    def my_hook(self, d):
        if self.stop_event.is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user")
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total_bytes and self.progress_callback:
                percent = downloaded / total_bytes
                self.progress_callback(percent)
        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback(1.0)
