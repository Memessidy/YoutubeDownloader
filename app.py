from tkinter.constants import END
import customtkinter
import threading
from CTkMessagebox import CTkMessagebox
from Downloader.downloader import YTDownloader
import pyperclip
from Utils.utils import resource_path


class MyCheckboxFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.count = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.entry = customtkinter.CTkEntry(self, placeholder_text="Enter URL here")
        self.entry.grid(column=0, row=0, padx=(10, 5), pady=(15, 5), sticky='we')

        self.paste_button = customtkinter.CTkButton(
            self, text='Paste', width=50, height=24, command=self.paste_from_clipboard
        )
        self.paste_button.grid(column=1, row=0, padx=(0, 10), pady=(15, 5))

        self.progress = customtkinter.CTkProgressBar(self)
        self.progress.grid(column=0, row=1, padx=(10, 5), pady=(5, 5), sticky="we")
        self.progress.set(0)

        self.label = customtkinter.CTkLabel(self, text="0 %", fg_color="transparent")
        self.label.grid(column=1, row=1, padx=(5, 10), pady=(5, 5), sticky='e')

        self.status_label = customtkinter.CTkLabel(self, text="", fg_color="transparent")
        self.status_label.grid(column=0, row=2, padx=0, pady=(5, 5), sticky='ew', columnspan=2)

    def paste_from_clipboard(self):
        self.entry.delete(0, END)
        self.entry.insert(0, pyperclip.paste())

    def set_progress(self, value: float):
        percent = int(value * 100)
        self.progress.set(value)
        self.label.configure(text=f"{percent}%")

        step_value = 'Downloading...'
        if percent == 100:
            self.count += 1
            if self.count % 2 == 0:
                step_value = 'Merging...'

        self.status_label.configure(text=step_value)

    def clear(self):
        self.progress.set(0)
        self.progress.grid_remove()
        self.label.grid_remove()
        self.status_label.grid_remove()

    def on_start(self):
        self.progress.grid()
        self.label.grid()
        self.status_label.grid()
        self.label.configure(text="0 %")
        self.status_label.configure(text="Downloading...")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader")
        self.geometry("500x180")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.resizable(False, False)

        self.checkbox_frame = MyCheckboxFrame(self)
        self.checkbox_frame.grid(column=0, row=0, sticky='nsew', pady=(15, 0))

        self.button = customtkinter.CTkButton(self, text="Download", command=self.toggle_download, fg_color='black')
        self.button.grid(column=0, row=1, sticky='nsew')

        self.downloader = None
        self.download_thread = None
        self.downloading = False
        self.checkbox_frame.clear()

    def clear_session(self):
        self.downloader = None
        self.download_thread = None
        self.downloading = False
        self.button.configure(text="Download", fg_color='black')
        self.checkbox_frame.clear()

    def toggle_download(self):
        url = self.checkbox_frame.entry.get().strip()
        if not url or len(url) > 250:
            CTkMessagebox(title="Error ❌", message="Enter URL!", icon="cancel")
            return
        elif self.downloading:
            self.stop_download()
            return

        self.button.configure(text="Cancel", fg_color="red")
        self.downloading = True
        self.checkbox_frame.on_start()

        self.downloader = YTDownloader(
            progress_callback=self.update_progress,
            finish_callback=self.download_finished,
            error_callback=self.download_error,
        )

        self.download_thread = threading.Thread(target=self.downloader.download_from_youtube, args=(url,))
        self.download_thread.start()

    def update_progress(self, value):
        self.after(0, lambda: self.checkbox_frame.set_progress(value))

    def download_finished(self):
        self.after(0, lambda: CTkMessagebox(title="Done ✅", message="Download complete!", icon="check"))
        self.clear_session()

    def download_error(self, message):
        self.after(0, lambda: CTkMessagebox(title="Error ❌", message=message, icon="cancel"))
        self.clear_session()

    def stop_download(self):
        if self.downloader:
            self.downloader.stop()
        if self.download_thread:
            self.download_thread.join(timeout=5.0)
        self.clear_session()
        CTkMessagebox(title="Cancelled", message="Download cancelled!", icon="info")


if __name__ == '__main__':
    app = App()
    icon_path = resource_path("icon.ico")
    app.iconbitmap(icon_path)
    app.mainloop()
