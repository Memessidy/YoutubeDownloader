import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import sys
import re
from typing import Optional
from downloader import YouTubeDownloader, get_js_runtimes




class YouTubeDownloaderGUI:
    """Графічний інтерфейс для YouTube Downloader"""

    def __init__(self, program_name: str):
        self.program_name = program_name
        self.root = ctk.CTk()

        self.root.iconbitmap(self.resource_path("icon.ico"))
        self.downloader = YouTubeDownloader()
        self.setup_callbacks()

        # Створюємо головне вікно
        self.root.title(self.program_name)
        self.root.geometry("550x580")
        self.root.resizable(False, False)

        # Центруємо вікно
        self.center_window()

        # Змінні
        self.current_title = ""
        self.available_qualities = []
        self.download_path = os.path.expanduser("~\Downloads")
        self.current_url = ""
        self.is_loading_info = False
        self.url_after_id = None

        # Створюємо інтерфейс
        self.create_widgets()

    @staticmethod
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def center_window(self):
        """Центрування вікна на екрані"""
        self.root.update_idletasks()
        width = 550
        height = 580
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_callbacks(self):
        """Налаштування callback-функцій для downloader"""
        self.downloader.set_callbacks(
            progress_callback=self.update_progress,
            status_callback=self.update_status,
            error_callback=self.show_error,
            complete_callback=self.download_complete
        )

    def validate_youtube_url(self, url: str) -> bool:
        """Перевірка, чи є посилання валідним YouTube-посиланням"""
        youtube_regex = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return bool(re.match(youtube_regex, url))

    def create_widgets(self):
        """Створення всіх елементів інтерфейсу"""

        # Основний контейнер
        self.main_frame = ctk.CTkFrame(self.root)
        # self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок (менший)
        title_label = ctk.CTkLabel(
            self.main_frame,
            text=self.program_name,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 15))

        # Поле для введення URL
        url_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        url_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            url_frame,
            text="Посилання на відео:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 3))

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=38
        )
        self.url_entry.pack(fill="x")

        # Індикатор завантаження
        self.loading_label = ctk.CTkLabel(
            url_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            height=15
        )
        self.loading_label.pack(anchor="w", pady=(2, 0))

        # Прив'язуємо події
        self.url_entry.bind("<KeyRelease>", self.on_url_change)
        self.url_entry.bind('<Control-V>', self.on_paste)
        self.url_entry.bind('<Command-V>', self.on_paste)
        self.url_entry.bind("<FocusOut>", self.on_focus_out)

        # Інформаційна картка (компактна)
        info_card = ctk.CTkFrame(self.main_frame, corner_radius=10)
        info_card.pack(fill="x", pady=(0, 10))

        # Заголовок картки
        ctk.CTkLabel(
            info_card,
            text="📹 Інформація про відео",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(8, 5), padx=10)

        # Назва відео
        self.title_label = ctk.CTkLabel(
            info_card,
            text="Очікування введення посилання...",
            wraplength=480,
            justify="left",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.title_label.pack(anchor="w", pady=(0, 5), padx=10)

        # Тривалість та якість в одному рядку
        info_row = ctk.CTkFrame(info_card, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 8), padx=10)

        self.duration_label = ctk.CTkLabel(
            info_row,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.duration_label.pack(side="left")

        self.quality_status = ctk.CTkLabel(
            info_row,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.quality_status.pack(side="right")

        # Панель вибору якості
        quality_frame = ctk.CTkFrame(self.main_frame)
        quality_frame.pack(fill="x", pady=(0, 10))

        quality_header = ctk.CTkFrame(quality_frame, fg_color="transparent")
        quality_header.pack(fill="x", padx=10, pady=(8, 5))

        ctk.CTkLabel(
            quality_header,
            text="Якість відео:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")


        self.quality_combo = ctk.CTkComboBox(
            quality_frame,
            values=["Доступно після отримання інформації"],
            state="disabled",
            height=32,
            font=ctk.CTkFont(size=12)
        )
        self.quality_combo.pack(fill="x", padx=10, pady=(0, 8))

        # Панель вибору шляху
        path_frame = ctk.CTkFrame(self.main_frame)
        path_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            path_frame,
            text="Зберегти в:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 5))

        path_controls = ctk.CTkFrame(path_frame, fg_color="transparent")
        path_controls.pack(fill="x", padx=10, pady=(0, 8))

        self.path_entry = ctk.CTkEntry(
            path_controls,
            textvariable=ctk.StringVar(value=self.download_path),
            height=32
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_button = ctk.CTkButton(
            path_controls,
            text="📁",
            command=self.browse_folder,
            width=40,
            height=32,
            font=ctk.CTkFont(size=14)
        )
        self.browse_button.pack(side="right")

        # Кнопка завантаження
        self.download_button = ctk.CTkButton(
            self.main_frame,
            text="⬇️ Завантажити відео",
            command=self.download_video,
            height=36,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20",
            state="disabled"
        )
        self.download_button.pack(pady=(5, 10))

        # Прогрес-бар
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, height=8)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)

        # Статус (компактний)
        status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        status_frame.pack(fill="x")

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Вставте посилання на YouTube-відео",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        self.speed_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="e"
        )
        self.speed_label.pack(side="right")

    def on_url_change(self, event=None):
        """Обробник зміни тексту в полі URL"""
        url = self.url_entry.get().strip()

        if self.url_after_id:
            self.root.after_cancel(self.url_after_id)

        if url:
            self.loading_label.configure(text="⏳ Очікування введення...")
            self.url_after_id = self.root.after(800, lambda: self.auto_get_info(url))
        else:
            self.loading_label.configure(text="")
            self.reset_info_panel()

    def on_paste(self, event=None):
        """Обробник вставлення тексту"""
        self.root.after(100, lambda: self.on_url_change())

    def on_focus_out(self, event=None):
        """Обробник втрати фокусу полем введення"""
        url = self.url_entry.get().strip()
        if url and not self.is_loading_info:
            self.auto_get_info(url)

    def auto_get_info(self, url: str):
        """Автоматичне отримання інформації про відео"""
        if not url:
            return

        if not self.validate_youtube_url(url):
            self.loading_label.configure(text="❌ Невірне посилання YouTube")
            self.status_label.configure(text="Будь ласка, введіть коректне посилання")
            self.reset_info_panel()
            return

        if self.is_loading_info:
            return

        self.current_url = url
        self.is_loading_info = True
        self.loading_label.configure(text="🔄 Отримання інформації...")
        self.status_label.configure(text="Отримання інформації про відео...")

        thread = threading.Thread(target=self._get_info_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def _get_info_thread(self, url: str):
        """Потік для отримання інформації"""
        title, qualities = self.downloader.get_video_info(url)

        duration = None
        try:
            import yt_dlp
            ydl_opts = {'quiet': True, 'no_warnings': True, 'noplaylist': True,
                        'js_runtimes': get_js_runtimes()}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                duration = info.get('duration')
        except:
            pass

        self.root.after(0, self._update_info_ui, title, qualities, duration)

    def _update_info_ui(self, title: Optional[str], qualities: list, duration: Optional[int] = None):
        """Оновлення інтерфейсу після отримання інформації"""
        self.is_loading_info = False
        self.loading_label.configure(text="")

        if title and qualities:
            self.current_title = title
            self.available_qualities = qualities

            display_title = title if len(title) <= 85 else title[:82] + "..."
            self.title_label.configure(text=f"📹 {display_title}")

            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"⏱️ {minutes}:{seconds:02d}"
                self.duration_label.configure(text=duration_str)

            # Відображаємо доступні якості
            self.quality_status.configure(text=f"🎬 {len(qualities)} якостей доступно")

            quality_strings = [f"{q}p" for q in qualities]
            self.quality_combo.configure(values=quality_strings, state="readonly")
            if quality_strings:
                default_quality = quality_strings[-1]
                self.quality_combo.set(default_quality)

            self.download_button.configure(state="normal")
            self.status_label.configure(
                text=f"✅ Готово до завантаження",
                text_color="green"
            )
            self.root.after(2000, lambda: self.status_label.configure(text_color="gray"))

        else:
            self.reset_info_panel()
            self.status_label.configure(
                text="❌ Не вдалося отримати інформацію",
                text_color="red"
            )
            self.loading_label.configure(text="❌ Помилка отримання інформації")

    def reset_info_panel(self):
        """Скидання інформаційної панелі"""
        self.current_title = ""
        self.available_qualities = []
        self.title_label.configure(text="Очікування введення посилання...")
        self.duration_label.configure(text="")
        self.quality_status.configure(text="")
        self.quality_combo.configure(values=["Недоступно"], state="disabled")
        self.quality_combo.set("Недоступно")
        self.download_button.configure(state="disabled")

    def browse_folder(self):
        """Вибір папки для збереження"""
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = folder
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def download_video(self):
        """Запуск завантаження відео"""
        if not self.current_url:
            messagebox.showwarning("Попередження", "Спочатку вставте посилання на відео")
            return

        quality_str = self.quality_combo.get()
        if not quality_str or quality_str == "Недоступно":
            messagebox.showwarning("Попередження", "Оберіть якість відео")
            return

        quality = int(quality_str.replace('p', ''))
        output_path = self.path_entry.get() or self.download_path

        # Вимикаємо кнопки під час завантаження
        self.download_button.configure(state="disabled", text="⏳ Завантаження...")
        self.browse_button.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        self.quality_combo.configure(state="disabled")

        self.progress_bar.set(0)
        self.speed_label.configure(text="")

        self.downloader.download_video(self.current_url, quality, output_path)

    def update_progress(self, percent: float, speed: float, eta: int):
        """Оновлення прогресу завантаження"""

        def update():
            self.progress_bar.set(percent / 100)

            if speed is not None and speed > 0:
                if speed < 1024:
                    speed_str = f"{speed:.0f} B/s"
                elif speed < 1024 * 1024:
                    speed_str = f"{speed / 1024:.1f} KB/s"
                else:
                    speed_str = f"{speed / (1024 * 1024):.1f} MB/s"

                if eta is not None and eta > 0:
                    if eta < 60:
                        eta_str = f"{eta}с"
                    else:
                        minutes = eta // 60
                        seconds = eta % 60
                        eta_str = f"{minutes}хв{seconds:02d}с"
                    self.speed_label.configure(text=f"{speed_str} | {eta_str}")
                else:
                    self.speed_label.configure(text=speed_str)

            self.status_label.configure(text=f"Завантаження: {percent:.1f}%")

        self.root.after(0, update)

    def update_status(self, status: str):
        """Оновлення статусу"""
        self.root.after(0, lambda: self.status_label.configure(text=status))

    def show_error(self, error_msg: str):
        """Показ помилки"""

        def show():
            self.reset_ui()
            self.progress_bar.set(0)
            self.speed_label.configure(text="")
            self.status_label.configure(text="❌ Помилка завантаження", text_color="red")
            messagebox.showerror("Помилка", error_msg)

        self.root.after(0, show)

    def download_complete(self):
        """Дії після завершення завантаження"""

        def complete():
            messagebox.showinfo(
                "Успіх",
                f"Відео успішно завантажено!\n{self.current_title[:50]}"
            )
            self.reset_ui()
            self.progress_bar.set(0)
            self.speed_label.configure(text="")
            self.status_label.configure(
                text="✅ Завантаження завершено!",
                text_color="green"
            )
            self.root.after(3000, lambda: self.status_label.configure(text_color="gray"))

        self.root.after(0, complete)

    def reset_ui(self):
        """Скидання інтерфейсу після завантаження"""
        self.download_button.configure(
            state="normal" if self.available_qualities else "disabled",
            text="⬇️ Завантажити відео"
        )
        self.browse_button.configure(state="normal")
        self.url_entry.configure(state="normal")
        self.quality_combo.configure(state="readonly" if self.available_qualities else "disabled")

    def run(self):
        """Запуск застосунку"""
        self.root.mainloop()


def main():
    """Головна функція"""
    # Налаштування теми customtkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = YouTubeDownloaderGUI(program_name='Завантажувач з ютубу 😎')
    app.run()


if __name__ == "__main__":
    main()
