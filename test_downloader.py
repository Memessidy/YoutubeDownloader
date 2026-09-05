import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from downloader import YouTubeDownloader


class DownloadResultTests(unittest.TestCase):
    def run_download(self, result=0, exception=None, content=b'video', hook=True):
        app = YouTubeDownloader()
        success, error = Mock(), Mock()
        app.set_callbacks(complete_callback=success, error_callback=error)
        app.is_downloading = True
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / 'video.mp4'
            if content is not None:
                filename.write_bytes(content)
            with patch('downloader.yt_dlp.YoutubeDL') as factory:
                def download(urls):
                    if exception:
                        raise exception
                    if hook:
                        factory.call_args.args[0]['post_hooks'][-1](str(filename))
                    return result
                factory.return_value.__enter__.return_value.download.side_effect = download
                app._download_thread('https://www.youtube.com/watch?v=CzzCZBXYXB4', {})
        self.assertFalse(app.is_downloading)
        return success, error

    def test_download_error_never_reports_success(self):
        success, error = self.run_download(exception=RuntimeError('HTTP 403'))
        success.assert_not_called()
        self.assertIn('HTTP 403', error.call_args.args[0])

    def test_nonzero_result_never_reports_success(self):
        success, error = self.run_download(result=1)
        success.assert_not_called()
        error.assert_called_once()

    def test_skipped_download_never_reports_success(self):
        success, error = self.run_download(hook=False)
        success.assert_not_called()
        error.assert_called_once()

    def test_missing_or_empty_file_never_reports_success(self):
        for content in (None, b''):
            with self.subTest(content=content):
                success, error = self.run_download(content=content)
                success.assert_not_called()
                error.assert_called_once()

    def test_completed_file_reports_success(self):
        success, error = self.run_download()
        success.assert_called_once_with()
        error.assert_not_called()


if __name__ == '__main__':
    unittest.main()
