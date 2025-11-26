"""
TranslatorUKR 1.0 - Програма для перекладу файлів на українську мову за допомогою LLM
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import time
from pathlib import Path
from openai import OpenAI
import json
import re
import ctypes

# Налаштування теми
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def set_dark_title_bar(window):
    """Встановлює темний title bar для вікна Windows"""
    try:
        window.update()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
        )
    except:
        pass  # Ігноруємо помилки на не-Windows системах


class TranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Конфігурація вікна
        self.title("🇺🇦 TranslatorUKR 1.0")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        
        # Змінні
        self.file_path = None
        self.original_lines = []
        self.translated_lines = []
        self.is_translating = False
        self.client = None
        
        # Статистика
        self.translation_start_time = None
        self.translated_count = 0
        
        # Глосарій термінів (власні переклади)
        self.glossary = {}
        self._load_glossary()
        
        # Історія файлів
        self.recent_files = []
        self._load_recent_files()
        
        # Автозбереження
        self.autosave_enabled = True
        self.autosave_interval = 30  # секунд
        
        # Ігри
        self.games_window = None
        
        # Провайдери API
        self.providers = {
            "OpenAI": {"url": "https://api.openai.com/v1", "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4.1-mini", "gpt-4.1", "o1-mini", "o1"], "needs_key": True},
            "Anthropic": {"url": "https://api.anthropic.com/v1", "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"], "needs_key": True},
            "DeepSeek": {"url": "https://api.deepseek.com/v1", "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"], "needs_key": True},
            "Google AI": {"url": "https://generativelanguage.googleapis.com/v1beta/openai", "models": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"], "needs_key": True},
            "Mistral": {"url": "https://api.mistral.ai/v1", "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "codestral-latest"], "needs_key": True},
            "Groq": {"url": "https://api.groq.com/openai/v1", "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"], "needs_key": True},
            "OpenRouter": {"url": "https://openrouter.ai/api/v1", "models": ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-exp:free", "deepseek/deepseek-chat"], "needs_key": True},
            "Together": {"url": "https://api.together.xyz/v1", "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "mistralai/Mixtral-8x7B-Instruct-v0.1", "Qwen/Qwen2.5-72B-Instruct-Turbo"], "needs_key": True},
            "Fireworks": {"url": "https://api.fireworks.ai/inference/v1", "models": ["accounts/fireworks/models/llama-v3p1-70b-instruct", "accounts/fireworks/models/mixtral-8x7b-instruct"], "needs_key": True},
            "Cerebras": {"url": "https://api.cerebras.ai/v1", "models": ["llama3.1-70b", "llama3.1-8b"], "needs_key": True},
            "Perplexity": {"url": "https://api.perplexity.ai", "models": ["llama-3.1-sonar-large-128k-chat", "llama-3.1-sonar-small-128k-chat"], "needs_key": True},
            "Cohere": {"url": "https://api.cohere.ai/v1", "models": ["command-r-plus", "command-r", "command"], "needs_key": True},
            "─── Локальні LLM ───": {"url": "", "models": [], "needs_key": False, "separator": True},
            "Ollama": {"url": "http://localhost:11434/v1", "models": ["llama3.2", "llama3.1", "mistral", "gemma2", "qwen2.5", "phi3", "deepseek-r1"], "needs_key": False},
            "LM Studio": {"url": "http://localhost:1234/v1", "models": ["local-model"], "needs_key": False},
            "LocalAI": {"url": "http://localhost:8080/v1", "models": ["gpt-4", "ggml-model"], "needs_key": False},
            "Text Gen WebUI": {"url": "http://localhost:5000/v1", "models": ["local-model"], "needs_key": False},
            "Jan": {"url": "http://localhost:1337/v1", "models": ["local-model"], "needs_key": False},
            "GPT4All": {"url": "http://localhost:4891/v1", "models": ["local-model"], "needs_key": False},
            "Kobold": {"url": "http://localhost:5001/v1", "models": ["local-model"], "needs_key": False},
            "vLLM": {"url": "http://localhost:8000/v1", "models": ["local-model"], "needs_key": False},
            "Власний URL": {"url": "", "models": [], "needs_key": True}
        }
        
        # Кольори
        self.colors = {
            "bg_dark": "#0d1117",
            "bg_card": "#161b22",
            "bg_input": "#21262d",
            "accent": "#58a6ff",
            "accent_hover": "#79b8ff",
            "success": "#3fb950",
            "warning": "#d29922",
            "text": "#c9d1d9",
            "text_muted": "#8b949e",
            "border": "#30363d",
            "ukr_blue": "#0057b7",
            "ukr_yellow": "#ffd700"
        }
        
        self.configure(fg_color=self.colors["bg_dark"])
        
        self._create_ui()
        self._load_settings()
        self._setup_hotkeys()
    
    def _create_ui(self):
        """Створення інтерфейсу"""
        
        # Головний контейнер
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === HEADER ===
        self._create_header()
        
        # === API SETTINGS ===
        self._create_api_settings()
        
        # === FILE CONTROLS ===
        self._create_file_controls()
        
        # === PROGRESS BAR ===
        self._create_progress_section()
        
        # === SEARCH & TOOLS ===
        self._create_tools_section()
        
        # === MAIN CONTENT - Side by Side ===
        self._create_content_area()
        
        # === FOOTER ===
        self._create_footer()
    
    def _create_header(self):
        """Створення заголовка"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=60)
        header_frame.pack(fill="x", pady=(0, 15))
        header_frame.pack_propagate(False)
        
        # Український прапор як декорація
        flag_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        flag_frame.pack(side="left")
        
        blue_bar = ctk.CTkFrame(flag_frame, fg_color=self.colors["ukr_blue"], 
                                 width=8, height=40, corner_radius=4)
        blue_bar.pack(side="left", padx=(0, 2))
        
        yellow_bar = ctk.CTkFrame(flag_frame, fg_color=self.colors["ukr_yellow"], 
                                   width=8, height=40, corner_radius=4)
        yellow_bar.pack(side="left")
        
        # Заголовок
        title_label = ctk.CTkLabel(
            header_frame, 
            text="TranslatorUKR",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=self.colors["text"]
        )
        title_label.pack(side="left", padx=15)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Переклад файлів на українську за допомогою ШІ",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_muted"]
        )
        subtitle_label.pack(side="left", pady=(8, 0))
        
        # Права частина header - кнопки
        right_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_frame.pack(side="right")
        
        # Статистика тексту
        self.stats_label = ctk.CTkLabel(
            right_frame, text="📊 0 слів | 0 символів",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        )
        self.stats_label.pack(side="left", padx=(0, 15))
        
        # Останні файли
        self.recent_menu_btn = ctk.CTkButton(
            right_frame, text="📂 Останні",
            width=100, height=32,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_input"],
            hover_color=self.colors["border"],
            command=self._show_recent_files
        )
        self.recent_menu_btn.pack(side="left", padx=(0, 10))
        
        # Міні-ігри
        self.games_btn = ctk.CTkButton(
            right_frame, text="🎮 Ігри",
            width=80, height=32,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_input"],
            hover_color=self.colors["border"],
            command=self._open_games_window
        )
        self.games_btn.pack(side="left", padx=(0, 10))
        
        # Допомога
        self.help_btn = ctk.CTkButton(
            right_frame, text="❓",
            width=35, height=32,
            font=ctk.CTkFont(size=14),
            fg_color=self.colors["bg_input"],
            hover_color=self.colors["border"],
            command=self._show_hotkeys_help
        )
        self.help_btn.pack(side="left")
    
    def _create_api_settings(self):
        """Налаштування API"""
        api_frame = ctk.CTkFrame(self.main_frame, fg_color=self.colors["bg_card"],
                                  corner_radius=12, border_width=1, 
                                  border_color=self.colors["border"])
        api_frame.pack(fill="x", pady=(0, 15))
        
        # Перший ряд - провайдер та API Key
        row1_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        row1_frame.pack(fill="x", padx=20, pady=(15, 8))
        
        # Провайдер
        ctk.CTkLabel(
            row1_frame, text="Провайдер:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text"]
        ).pack(side="left", padx=(0, 10))
        
        provider_names = list(self.providers.keys())
        self.provider_var = ctk.StringVar(value="OpenAI")
        self.provider_menu = ctk.CTkOptionMenu(
            row1_frame, width=180, height=38,
            values=provider_names,
            variable=self.provider_var,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_input"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            dropdown_fg_color=self.colors["bg_card"],
            dropdown_hover_color=self.colors["bg_input"],
            command=self._on_provider_change
        )
        self.provider_menu.pack(side="left", padx=(0, 20))
        
        # Індикатор локальної моделі
        self.local_indicator = ctk.CTkLabel(
            row1_frame, text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["success"]
        )
        self.local_indicator.pack(side="left", padx=(0, 20))
        
        # API Key
        self.api_key_label = ctk.CTkLabel(
            row1_frame, text="API Key:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text"]
        )
        self.api_key_label.pack(side="left", padx=(0, 10))
        
        self.api_key_entry = ctk.CTkEntry(
            row1_frame, width=400, height=38,
            placeholder_text="sk-... або ваш API ключ",
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text"],
            show="•"
        )
        self.api_key_entry.pack(side="left", padx=(0, 20))
        
        # Save button
        self.save_api_btn = ctk.CTkButton(
            row1_frame, text="💾 Зберегти",
            width=120, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.colors["bg_input"],
            hover_color=self.colors["border"],
            border_width=1,
            border_color=self.colors["border"],
            command=self._save_settings
        )
        self.save_api_btn.pack(side="right")
        
        # Другий ряд - URL та модель
        row2_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        row2_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Base URL
        ctk.CTkLabel(
            row2_frame, text="Base URL:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text"]
        ).pack(side="left", padx=(0, 10))
        
        self.base_url_entry = ctk.CTkEntry(
            row2_frame, width=400, height=38,
            placeholder_text="https://api.openai.com/v1",
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text"]
        )
        self.base_url_entry.pack(side="left", padx=(0, 20))
        
        # Model
        ctk.CTkLabel(
            row2_frame, text="Модель:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text"]
        ).pack(side="left", padx=(0, 10))
        
        self.model_var = ctk.StringVar(value="gpt-4o-mini")
        self.model_menu = ctk.CTkOptionMenu(
            row2_frame, width=280, height=38,
            values=self.providers["OpenAI"]["models"],
            variable=self.model_var,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_input"],
            button_color=self.colors["accent"],
            button_hover_color=self.colors["accent_hover"],
            dropdown_fg_color=self.colors["bg_card"],
            dropdown_hover_color=self.colors["bg_input"]
        )
        self.model_menu.pack(side="left", padx=(0, 15))
        
        # Custom model entry (для власних моделей)
        self.custom_model_entry = ctk.CTkEntry(
            row2_frame, width=200, height=38,
            placeholder_text="або введіть назву моделі",
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text"]
        )
        self.custom_model_entry.pack(side="left")
        
        # Кнопка тестування з'єднання
        self.test_btn = ctk.CTkButton(
            row2_frame, text="🔌 Тест",
            width=80, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.colors["success"],
            hover_color="#2ea043",
            command=self._test_connection
        )
        self.test_btn.pack(side="right")
    
    def _on_provider_change(self, provider_name):
        """Обробка зміни провайдера"""
        if provider_name.startswith("───"):
            # Це роздільник, повертаємо попередній вибір
            self.provider_var.set("Ollama")
            provider_name = "Ollama"
        
        provider = self.providers.get(provider_name, {})
        
        # Оновлюємо URL
        self.base_url_entry.delete(0, "end")
        if provider.get("url"):
            self.base_url_entry.insert(0, provider["url"])
        
        # Оновлюємо список моделей
        models = provider.get("models", [])
        if models:
            self.model_menu.configure(values=models)
            self.model_var.set(models[0])
        else:
            self.model_menu.configure(values=["custom"])
            self.model_var.set("custom")
        
        # Показуємо/ховаємо поле API Key
        needs_key = provider.get("needs_key", True)
        if needs_key:
            self.api_key_label.configure(text_color=self.colors["text"])
            self.api_key_entry.configure(state="normal", placeholder_text="sk-... або ваш API ключ")
            self.local_indicator.configure(text="")
        else:
            self.api_key_label.configure(text_color=self.colors["text_muted"])
            self.api_key_entry.configure(state="normal", placeholder_text="Не потрібен для локальних моделей")
            self.local_indicator.configure(text="🏠 Локальна модель")
        
        self._update_status(f"Вибрано: {provider_name}", self.colors["accent"])
    
    def _test_connection(self):
        """Тестування з'єднання з API"""
        def test_thread():
            try:
                api_key = self.api_key_entry.get() or "not-needed"
                base_url = self.base_url_entry.get()
                
                if not base_url:
                    self.after(0, lambda: self._update_status("❌ Введіть Base URL", "#da3633"))
                    return
                
                client = OpenAI(api_key=api_key, base_url=base_url, timeout=10)
                
                # Спробуємо отримати список моделей
                try:
                    models = client.models.list()
                    model_names = [m.id for m in models.data][:5]
                    self.after(0, lambda: self._update_status(
                        f"✅ З'єднання успішне! Моделі: {', '.join(model_names)}...", 
                        self.colors["success"]
                    ))
                    
                    # Оновлюємо список моделей якщо отримали
                    if model_names:
                        self.after(0, lambda: self._update_model_list(model_names))
                except:
                    # Якщо не можемо отримати моделі, просто перевіряємо чи відповідає сервер
                    self.after(0, lambda: self._update_status(
                        "✅ Сервер відповідає (список моделей недоступний)", 
                        self.colors["success"]
                    ))
                    
            except Exception as e:
                error_msg = str(e)[:50]
                self.after(0, lambda: self._update_status(f"❌ Помилка: {error_msg}", "#da3633"))
        
        self._update_status("🔄 Тестування з'єднання...", self.colors["warning"])
        threading.Thread(target=test_thread, daemon=True).start()
    
    def _update_model_list(self, models):
        """Оновлення списку моделей"""
        current_models = list(self.model_menu.cget("values"))
        all_models = list(set(current_models + models))
        self.model_menu.configure(values=all_models)
    
    def _create_file_controls(self):
        """Контроли для файлів"""
        controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 15))
        
        # Вибір файлу
        self.file_btn = ctk.CTkButton(
            controls_frame, text="📂 Вибрати файл",
            width=160, height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            text_color="white",
            text_color_disabled="white",
            command=self._select_file
        )
        self.file_btn.pack(side="left", padx=(0, 15))
        
        # Шлях до файлу
        self.file_label = ctk.CTkLabel(
            controls_frame,
            text="Файл не вибрано",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_muted"]
        )
        self.file_label.pack(side="left", padx=(0, 20))
        
        # Кнопка перекладу
        self.translate_btn = ctk.CTkButton(
            controls_frame, text="🚀 Почати переклад",
            width=180, height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["success"],
            hover_color="#2ea043",
            text_color="white",
            text_color_disabled="white",
            command=self._start_translation,
            state="disabled"
        )
        self.translate_btn.pack(side="left", padx=(0, 15))
        
        # Кнопка зупинки
        self.stop_btn = ctk.CTkButton(
            controls_frame, text="⏹ Зупинити",
            width=140, height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#da3633",
            hover_color="#b62324",
            text_color="white",
            text_color_disabled="white",
            command=self._stop_translation,
            state="disabled"
        )
        self.stop_btn.pack(side="left")
        
        # Кнопка збереження
        self.save_btn = ctk.CTkButton(
            controls_frame, text="💾 Зберегти переклад",
            width=180, height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["ukr_blue"],
            hover_color="#0066cc",
            command=self._save_translation,
            state="disabled"
        )
        self.save_btn.pack(side="right")
        
        # Підказка про Ctrl+C
        hint_label = ctk.CTkLabel(
            controls_frame,
            text="💡 Якщо Ctrl+C/V не працює, переключіть системну мову на англійську",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        )
        hint_label.pack(side="right", padx=(0, 20))
    
    def _create_progress_section(self):
        """Секція прогресу"""
        progress_frame = ctk.CTkFrame(self.main_frame, fg_color=self.colors["bg_card"],
                                       corner_radius=12, border_width=1,
                                       border_color=self.colors["border"])
        progress_frame.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(progress_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=12)
        
        # Статус
        self.status_label = ctk.CTkLabel(
            inner, text="⏳ Очікування...",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_muted"]
        )
        self.status_label.pack(side="left")
        
        # Статистика швидкості
        self.speed_label = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"]
        )
        self.speed_label.pack(side="left", padx=(20, 0))
        
        # Лічильник рядків
        self.lines_label = ctk.CTkLabel(
            inner, text="0 / 0 рядків",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["accent"]
        )
        self.lines_label.pack(side="right")
        
        # Прогрес бар
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame, height=8,
            fg_color=self.colors["bg_input"],
            progress_color=self.colors["ukr_yellow"]
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 12))
        self.progress_bar.set(0)
    
    def _create_tools_section(self):
        """Секція інструментів: пошук та глосарій"""
        tools_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        tools_frame.pack(fill="x", pady=(0, 10))
        
        # === ПОШУК ===
        search_frame = ctk.CTkFrame(tools_frame, fg_color=self.colors["bg_card"],
                                     corner_radius=10, border_width=1,
                                     border_color=self.colors["border"])
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            search_inner, text="🔍",
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=(0, 8))
        
        self.search_entry = ctk.CTkEntry(
            search_inner, width=250, height=32,
            placeholder_text="Пошук в тексті... (Ctrl+F)",
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_input"],
            border_color=self.colors["border"],
            text_color=self.colors["text"]
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._search_text())
        
        ctk.CTkButton(
            search_inner, text="Знайти",
            width=80, height=32,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            command=self._search_text
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            search_inner, text="▼",
            width=32, height=32,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_input"],
            hover_color=self.colors["border"],
            command=self._search_next
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            search_inner, text="▲",
            width=32, height=32,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_input"],
            hover_color=self.colors["border"],
            command=self._search_prev
        ).pack(side="left")
        
        self.search_result_label = ctk.CTkLabel(
            search_inner, text="",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        )
        self.search_result_label.pack(side="left", padx=(15, 0))
        
        # === ГЛОСАРІЙ ===
        glossary_frame = ctk.CTkFrame(tools_frame, fg_color=self.colors["bg_card"],
                                       corner_radius=10, border_width=1,
                                       border_color=self.colors["border"])
        glossary_frame.pack(side="right")
        
        glossary_inner = ctk.CTkFrame(glossary_frame, fg_color="transparent")
        glossary_inner.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            glossary_inner, text="📚",
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(
            glossary_inner, text=f"Глосарій: {len(self.glossary)} термінів",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"]
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            glossary_inner, text="✏️ Редагувати",
            width=110, height=32,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors["bg_input"],
            hover_color=self.colors["border"],
            command=self._open_glossary_editor
        ).pack(side="left")
        
        # Змінні для пошуку
        self.search_matches = []
        self.current_match = 0
    
    def _create_content_area(self):
        """Область контенту - два текстових поля поруч"""
        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Конфігурація grid
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # === ОРИГІНАЛ ===
        original_frame = ctk.CTkFrame(content_frame, fg_color=self.colors["bg_card"],
                                       corner_radius=12, border_width=1,
                                       border_color=self.colors["border"])
        original_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        # Заголовок оригіналу
        orig_header = ctk.CTkFrame(original_frame, fg_color=self.colors["bg_input"],
                                    corner_radius=0, height=45)
        orig_header.pack(fill="x")
        orig_header.pack_propagate(False)
        
        ctk.CTkLabel(
            orig_header, text="📄 ОРИГІНАЛ",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        ).pack(side="left", padx=15, pady=10)
        
        # Кнопка копіювання оригіналу
        ctk.CTkButton(
            orig_header, text="📋",
            width=35, height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=self.colors["border"],
            command=lambda: self._copy_to_clipboard("original")
        ).pack(side="right", padx=(0, 5))
        
        self.original_lines_label = ctk.CTkLabel(
            orig_header, text="0 рядків",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"]
        )
        self.original_lines_label.pack(side="right", padx=(15, 5))
        
        # Текстове поле оригіналу
        self.original_text = ctk.CTkTextbox(
            original_frame, 
            font=ctk.CTkFont(family="JetBrains Mono, Cascadia Code, Fira Code, Consolas", size=13),
            fg_color="#0d1117",
            text_color="#e6edf3",
            wrap="none",
            activate_scrollbars=True,
            corner_radius=8
        )
        self.original_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Налаштування тегів для підсвітки синтаксису (оригінал)
        self._setup_syntax_tags(self.original_text)
        
        # === ПЕРЕКЛАД ===
        translated_frame = ctk.CTkFrame(content_frame, fg_color=self.colors["bg_card"],
                                         corner_radius=12, border_width=1,
                                         border_color=self.colors["border"])
        translated_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        # Заголовок перекладу
        trans_header = ctk.CTkFrame(translated_frame, fg_color=self.colors["ukr_blue"],
                                     corner_radius=0, height=45)
        trans_header.pack(fill="x")
        trans_header.pack_propagate(False)
        
        ctk.CTkLabel(
            trans_header, text="🇺🇦 УКРАЇНСЬКИЙ ПЕРЕКЛАД",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=15, pady=10)
        
        # Кнопка редагування
        self.edit_btn = ctk.CTkButton(
            trans_header, text="✏️ Редагувати",
            width=100, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color="#003d80",
            text_color="white",
            command=self._toggle_edit_mode
        )
        self.edit_btn.pack(side="right", padx=(0, 5))
        
        # Кнопка копіювання перекладу
        ctk.CTkButton(
            trans_header, text="📋",
            width=35, height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#003d80",
            text_color="white",
            command=lambda: self._copy_to_clipboard("translated")
        ).pack(side="right", padx=(0, 5))
        
        self.translated_lines_label = ctk.CTkLabel(
            trans_header, text="0 рядків",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["ukr_yellow"]
        )
        self.translated_lines_label.pack(side="right", padx=(15, 5))
        
        # Текстове поле перекладу
        self.translated_text = ctk.CTkTextbox(
            translated_frame,
            font=ctk.CTkFont(family="JetBrains Mono, Cascadia Code, Fira Code, Consolas", size=13),
            fg_color="#0a0e14",
            text_color="#e6edf3",
            wrap="none",
            activate_scrollbars=True,
            corner_radius=8
        )
        self.translated_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Налаштування тегів для підсвітки синтаксису (переклад)
        self._setup_syntax_tags(self.translated_text, is_translation=True)
        
        # Синхронізація скролу
        self._sync_scroll()
    
    def _setup_syntax_tags(self, textbox, is_translation=False):
        """Налаштування тегів для підсвітки синтаксису"""
        # Отримуємо внутрішній текстовий віджет
        inner_text = textbox._textbox
        
        # Кольори для різних елементів
        if is_translation:
            # Переклад - жовтуваті/теплі тони
            inner_text.tag_configure("key", foreground="#79c0ff")        # Ключі - блакитний
            inner_text.tag_configure("string", foreground="#ffd700")     # Рядки - золотий
            inner_text.tag_configure("number", foreground="#ff9f43")     # Числа - помаранчевий
            inner_text.tag_configure("bracket", foreground="#8b949e")    # Дужки - сірий
            inner_text.tag_configure("placeholder", foreground="#f97583")# Плейсхолдери - рожевий
            inner_text.tag_configure("tag", foreground="#7ee787")        # Теги - зелений
            inner_text.tag_configure("comment", foreground="#6e7681", font=("JetBrains Mono", 12, "italic"))
            inner_text.tag_configure("speaker", foreground="#d2a8ff", font=("JetBrains Mono", 13, "bold"))
        else:
            # Оригінал - холодніші тони
            inner_text.tag_configure("key", foreground="#79c0ff")        # Ключі - блакитний
            inner_text.tag_configure("string", foreground="#a5d6ff")     # Рядки - світло-блакитний
            inner_text.tag_configure("number", foreground="#79c0ff")     # Числа - блакитний
            inner_text.tag_configure("bracket", foreground="#6e7681")    # Дужки - темно-сірий
            inner_text.tag_configure("placeholder", foreground="#ff7b72")# Плейсхолдери - червоний
            inner_text.tag_configure("tag", foreground="#7ee787")        # Теги - зелений
            inner_text.tag_configure("comment", foreground="#6e7681", font=("JetBrains Mono", 12, "italic"))
            inner_text.tag_configure("speaker", foreground="#d2a8ff", font=("JetBrains Mono", 13, "bold"))
        
        # Номери рядків
        inner_text.tag_configure("line_num", foreground="#484f58")
    
    def _apply_syntax_highlighting(self, textbox, content):
        """Застосування підсвітки синтаксису до тексту"""
        inner_text = textbox._textbox
        
        # Очищаємо теги
        for tag in ["key", "string", "number", "bracket", "placeholder", "tag", "comment", "speaker"]:
            inner_text.tag_remove(tag, "1.0", "end")
        
        lines = content.split("\n")
        
        for line_num, line in enumerate(lines, 1):
            line_start = f"{line_num}.0"
            
            # Спікер [SPEAKER: Name]
            for match in re.finditer(r'\[[A-Z_]+:[^\]]+\]', line):
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end()}"
                inner_text.tag_add("speaker", start, end)
            
            # JSON ключі "key":
            for match in re.finditer(r'"[^"]+"\s*:', line):
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end() - 1}"
                inner_text.tag_add("key", start, end)
            
            # Рядки в лапках
            for match in re.finditer(r'"[^"]*"', line):
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end()}"
                inner_text.tag_add("string", start, end)
            
            # Плейсхолдери {var}, %s, $var
            for match in re.finditer(r'\{[^}]+\}|%[sdif]|\$\w+', line):
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end()}"
                inner_text.tag_add("placeholder", start, end)
            
            # HTML/XML теги
            for match in re.finditer(r'<[^>]+>', line):
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end()}"
                inner_text.tag_add("tag", start, end)
            
            # Числа
            for match in re.finditer(r'\b\d+\.?\d*\b', line):
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end()}"
                inner_text.tag_add("number", start, end)
            
            # Дужки
            for match in re.finditer(r'[\[\]{}(),]', line):
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end()}"
                inner_text.tag_add("bracket", start, end)
            
            # Коментарі
            for match in re.finditer(r'//.*$|#.*$', line):
                start = f"{line_num}.{match.start()}"
                end = f"{line_num}.{match.end()}"
                inner_text.tag_add("comment", start, end)
    
    def _sync_scroll(self):
        """Синхронізація скролу між двома текстовими полями"""
        def on_scroll_original(*args):
            self.translated_text.yview_moveto(args[0])
        
        def on_scroll_translated(*args):
            self.original_text.yview_moveto(args[0])
        
        # Bind mouse wheel
        def on_mousewheel_original(event):
            self.translated_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def on_mousewheel_translated(event):
            self.original_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.original_text.bind("<MouseWheel>", on_mousewheel_original)
        self.translated_text.bind("<MouseWheel>", on_mousewheel_translated)
    
    def _create_footer(self):
        """Footer з інформацією"""
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=30)
        footer_frame.pack(fill="x")
        
        ctk.CTkLabel(
            footer_frame,
            text="TranslatorUKR 1.0 • Створено з 💙💛 для України",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        ).pack(side="left")
        
        ctk.CTkLabel(
            footer_frame,
            text="Підтримує: OpenAI, Anthropic, Groq, OpenRouter та інші OpenAI-сумісні API",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_muted"]
        ).pack(side="right")
    
    def _load_settings(self):
        """Завантаження налаштувань"""
        settings_file = Path("translator_settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    
                    # Провайдер
                    provider = settings.get("provider", "OpenAI")
                    if provider in self.providers:
                        self.provider_var.set(provider)
                        self._on_provider_change(provider)
                    
                    # API Key
                    self.api_key_entry.delete(0, "end")
                    self.api_key_entry.insert(0, settings.get("api_key", ""))
                    
                    # Base URL
                    self.base_url_entry.delete(0, "end")
                    self.base_url_entry.insert(0, settings.get("base_url", "https://api.openai.com/v1"))
                    
                    # Model
                    model = settings.get("model", "gpt-4o-mini")
                    self.model_var.set(model)
                    
                    # Custom model
                    custom_model = settings.get("custom_model", "")
                    if custom_model:
                        self.custom_model_entry.insert(0, custom_model)
            except:
                pass
    
    def _save_settings(self):
        """Збереження налаштувань"""
        settings = {
            "provider": self.provider_var.get(),
            "api_key": self.api_key_entry.get(),
            "base_url": self.base_url_entry.get() or "https://api.openai.com/v1",
            "model": self.model_var.get(),
            "custom_model": self.custom_model_entry.get()
        }
        with open("translator_settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        
        self._update_status("✅ Налаштування збережено!", self.colors["success"])
    
    def _select_file(self):
        """Вибір файлу для перекладу"""
        file_path = filedialog.askopenfilename(
            title="Виберіть файл для перекладу",
            filetypes=[
                ("Всі файли", "*.*"),
                ("Файли локалізації", "*.json;*.xml;*.txt;*.ini;*.yaml;*.yml;*.po;*.pot;*.lua;*.csv;*.lang;*.properties"),
                ("JSON", "*.json"),
                ("XML", "*.xml"),
                ("YAML", "*.yaml;*.yml"),
                ("INI/Properties", "*.ini;*.properties"),
                ("PO/POT (Gettext)", "*.po;*.pot"),
                ("Lua", "*.lua"),
                ("CSV", "*.csv"),
                ("Текстові файли", "*.txt"),
                ("SubRip Subtitles", "*.srt")
            ]
        )
        
        if file_path:
            self.file_path = file_path
            self.file_label.configure(text=f"📄 {Path(file_path).name}")
            self._load_file()
    
    def _load_file(self):
        """Завантаження файлу"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.original_lines = content.split("\n")
            self.translated_lines = [""] * len(self.original_lines)
            
            # Відображення в текстовому полі
            self.original_text.delete("1.0", "end")
            self.original_text.insert("1.0", content)
            
            self.translated_text.delete("1.0", "end")
            
            # Оновлення лічильників
            total_lines = len(self.original_lines)
            self.original_lines_label.configure(text=f"{total_lines} рядків")
            self.lines_label.configure(text=f"0 / {total_lines} рядків")
            
            self.translate_btn.configure(state="normal")
            self._update_status(f"📂 Файл завантажено: {total_lines} рядків", self.colors["accent"])
            
            # Додати в історію
            self._add_to_recent(self.file_path)
            
            # Оновити статистику
            self._update_text_stats()
            
            # Застосувати підсвітку синтаксису
            self.after(100, lambda: self._apply_syntax_highlighting(self.original_text, content))
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити файл:\n{str(e)}")
    
    def _start_translation(self):
        """Початок перекладу"""
        provider = self.provider_var.get()
        needs_key = self.providers.get(provider, {}).get("needs_key", True)
        
        api_key = self.api_key_entry.get()
        if needs_key and not api_key:
            messagebox.showwarning("Увага", "Введіть API ключ!")
            return
        
        # Для локальних моделей використовуємо фіктивний ключ
        if not api_key:
            api_key = "not-needed"
        
        base_url = self.base_url_entry.get()
        if not base_url:
            messagebox.showwarning("Увага", "Введіть Base URL!")
            return
        
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося підключитися до API:\n{str(e)}")
            return
        
        self.is_translating = True
        self.translate_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.file_btn.configure(state="disabled")
        
        # Запуск перекладу в окремому потоці
        thread = threading.Thread(target=self._translate_worker, daemon=True)
        thread.start()
        
        # Запуск автозбереження
        self._start_autosave()
    
    def _translate_worker(self):
        """Робочий потік для перекладу"""
        # Використовуємо кастомну модель якщо вказана, інакше з меню
        model = self.custom_model_entry.get().strip() or self.model_var.get()
        total_lines = len(self.original_lines)
        
        self.translated_text.delete("1.0", "end")
        self.translated_lines = []
        
        # Статистика
        self.translation_start_time = time.time()
        self.translated_count = 0
        
        # Відстеження блоків коду (``` ... ```)
        inside_code_block = False
        
        for i, line in enumerate(self.original_lines):
            if not self.is_translating:
                break
            
            # Оновлення статусу
            self.after(0, lambda idx=i: self._update_progress(idx, total_lines))
            
            stripped = line.strip()
            
            # Перевірка на початок/кінець блоку коду
            if stripped.startswith('```'):
                inside_code_block = not inside_code_block
                translated_line = line  # Копіюємо маркер ``` як є
            # Якщо всередині блоку коду - не перекладаємо
            elif inside_code_block:
                translated_line = line
            # Якщо рядок порожній, таймстамп або код - копіюємо як є
            elif not stripped or self._is_timestamp(line) or self._is_code_line(line):
                translated_line = line
            else:
                # Витягуємо текст для перекладу зі збереженням структури
                prefix, text_to_translate, suffix, placeholders = self._extract_translatable_text(line)
                
                # Якщо немає тексту для перекладу - копіюємо як є
                if not text_to_translate.strip():
                    translated_line = line
                else:
                    # Перекладаємо тільки текст
                    translated_text = self._translate_line(text_to_translate, model, placeholders)
                    
                    # Відновлюємо плейсхолдери
                    translated_text = self._restore_placeholders(text_to_translate, translated_text, placeholders)
                    
                    # Збираємо рядок назад
                    translated_line = prefix + translated_text + suffix
            
            self.translated_lines.append(translated_line)
            
            # Додавання перекладеного рядка в реальному часі
            self.after(0, lambda text=translated_line, idx=i: self._append_translated(text, idx))
        
        # Завершення
        self.after(0, self._translation_complete)
    
    def _is_timestamp(self, line):
        """Перевірка чи рядок є таймстампом (для субтитрів)"""
        # SRT timestamp pattern: 00:00:00,000 --> 00:00:00,000
        pattern = r'^\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}$'
        return bool(re.match(pattern, line.strip()))
    
    def _is_code_line(self, line):
        """Перевірка чи рядок є кодом/технічним рядком (не перекладати)"""
        stripped = line.strip()
        
        # Порожній рядок
        if not stripped:
            return True
        
        # Тільки числа
        if stripped.isdigit():
            return True
        
        # Блок коду markdown (```)
        if stripped.startswith('```'):
            return True
        
        # Теги [SPEAKER: ...], [CHARACTER: ...] тощо
        if re.match(r'^\[[A-Z_]+:\s*[^\]]+\]$', stripped):
            return True
        
        # Коментарі (різні формати)
        if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*/'):
            return True
        if stripped.startswith('#') and not stripped.startswith('##'):
            return True
        if stripped.startswith('--') and not stripped.startswith('---'):
            return True
        if stripped.startswith(';') or stripped.startswith('<!--') or stripped.startswith('-->'):
            return True
        
        # Чисто структурні символи JSON/XML/Python
        if stripped in ['{', '}', '[', ']', ',', '};', '},', '];', '],', '(', ')', '):']:
            return True
        
        # JSON/Python структурні рядки
        # Список/масив: dialogue_data = [
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[\[\{]$', stripped):
            return True
        
        # Булеві/None значення в JSON/Python
        if re.match(r'^["\']?is_code["\']?\s*:\s*(True|False|true|false),?$', stripped, re.IGNORECASE):
            return True
        if re.match(r'^["\']?[a-zA-Z_]+["\']?\s*:\s*(True|False|true|false|None|null|\d+),?$', stripped, re.IGNORECASE):
            return True
        
        # Закриваючі/самозакриваючі теги XML
        if re.match(r'^<\/[^>]+>$', stripped) or re.match(r'^<[^>]+\/>$', stripped):
            return True
        
        # Відкриваючий тег без тексту
        if re.match(r'^<[a-zA-Z_][^>]*>$', stripped) and '>' not in stripped[1:-1]:
            return True
            
        return False
    
    def _extract_translatable_text(self, line):
        """
        Витягує текст для перекладу зі збереженням структури.
        Повертає: (prefix, text_to_translate, suffix, placeholders)
        """
        # Зберігаємо початкові пробіли/відступи
        leading_spaces = len(line) - len(line.lstrip())
        indent = line[:leading_spaces]
        stripped = line.strip()
        
        # === Формат KEY { text } (Unreal, деякі ігрові движки) ===
        # Текст може містити будь-які символи крім закриваючої дужки
        key_brace_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\{\s*(.+)\s*\}$', stripped, re.DOTALL)
        if key_brace_match:
            key, value = key_brace_match.groups()
            value = value.strip()
            if value:
                prefix = f'{indent}{key} {{ '
                suffix = ' }'
                placeholders = self._extract_placeholders(value)
                return prefix, value, suffix, placeholders
        
        # === Формат тільки { text } без ключа ===
        brace_only_match = re.match(r'^\{\s*(.+)\s*\}$', stripped, re.DOTALL)
        if brace_only_match:
            value = brace_only_match.group(1).strip()
            if value:
                prefix = f'{indent}{{ '
                suffix = ' }'
                placeholders = self._extract_placeholders(value)
                return prefix, value, suffix, placeholders
        
        # === JSON формат: "key": "value" ===
        # Шукаємо патерн "ключ": "значення" або 'ключ': 'значення'
        json_match = re.match(r'^(["\'])([^"\']+)\1\s*:\s*(["\'])(.*)(\3)\s*(,?)$', stripped)
        if json_match:
            key_quote, key, val_quote, value, _, comma = json_match.groups()
            
            # Список ключів які НЕ перекладаємо (системні ключі)
            skip_keys = ['speaker', 'id', 'key', 'name', 'type', 'class', 'tag', 'is_code', 
                         'code', 'script', 'function', 'method', 'variable', 'path', 'file',
                         'icon', 'image', 'sound', 'audio', 'animation', 'sprite', 'texture']
            
            # Якщо ключ системний - не перекладаємо значення
            if key.lower() in skip_keys:
                return indent, "", "", []
            
            # Перекладаємо тільки VALUE якщо це текстовий контент
            # (message, text, description, title, label, hint, tooltip, dialogue, etc.)
            translatable_keys = ['message', 'text', 'description', 'title', 'label', 'hint',
                                 'tooltip', 'dialogue', 'dialog', 'content', 'body', 'value',
                                 'caption', 'placeholder', 'button', 'option', 'choice',
                                 'question', 'answer', 'reply', 'response', 'note', 'warning',
                                 'error', 'success', 'info', 'help', 'about', 'summary']
            
            if value.strip() and key.lower() in translatable_keys:
                prefix = f'{indent}{key_quote}{key}{key_quote}: {val_quote}'
                suffix = f'{val_quote}{comma}'
                placeholders = self._extract_placeholders(value)
                return prefix, value, suffix, placeholders
            
            return indent, "", "", []  # Ключ не в списку - не перекладаємо
        
        # === JSON просте значення: "value" або "value", ===
        json_simple = re.match(r'^(["\'])(.+)\1\s*(,?)$', stripped)
        if json_simple:
            quote, value, comma = json_simple.groups()
            # Перевіряємо чи це не ключ (немає двокрапки далі - це значення)
            if value.strip():
                prefix = f'{indent}{quote}'
                suffix = f'{quote}{comma}'
                placeholders = self._extract_placeholders(value)
                return prefix, value, suffix, placeholders
        
        # === XML формат: <tag attr="x">text</tag> ===
        xml_match = re.match(r'^(<[^>]+>)(.+)(<\/[^>]+>)$', stripped)
        if xml_match:
            open_tag, content, close_tag = xml_match.groups()
            if content.strip():
                prefix = f'{indent}{open_tag}'
                suffix = close_tag
                placeholders = self._extract_placeholders(content)
                return prefix, content, suffix, placeholders
        
        # === INI формат: key=value ===
        ini_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_\.]*)\s*=\s*(.+)$', stripped)
        if ini_match:
            key, value = ini_match.groups()
            # Перевіряємо чи значення не є числом або булевим
            if not re.match(r'^-?\d+\.?\d*$', value) and value.lower() not in ['true', 'false', 'yes', 'no', 'null', 'none']:
                # Видаляємо лапки якщо є
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    inner_value = value[1:-1]
                    prefix = f'{indent}{key}={value[0]}'
                    suffix = value[-1]
                else:
                    inner_value = value
                    prefix = f'{indent}{key}='
                    suffix = ''
                placeholders = self._extract_placeholders(inner_value)
                return prefix, inner_value, suffix, placeholders
        
        # === YAML формат: key: value або key: "value" ===
        yaml_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_\-]*)\s*:\s*(.+)$', stripped)
        if yaml_match:
            key, value = yaml_match.groups()
            # Пропускаємо якщо значення - список або об'єкт
            if not value.startswith('[') and not value.startswith('{'):
                # Видаляємо лапки
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    inner_value = value[1:-1]
                    prefix = f'{indent}{key}: {value[0]}'
                    suffix = value[-1]
                else:
                    inner_value = value
                    prefix = f'{indent}{key}: '
                    suffix = ''
                # Пропускаємо числа та булеві
                if not re.match(r'^-?\d+\.?\d*$', inner_value) and inner_value.lower() not in ['true', 'false', 'yes', 'no', 'null', '~']:
                    placeholders = self._extract_placeholders(inner_value)
                    return prefix, inner_value, suffix, placeholders
        
        # === Lua формат: ["key"] = "value" або key = "value" ===
        lua_match = re.match(r'^(\[?["\']?[^\]"\']+["\']?\]?\s*=\s*)(["\'])(.*)(\2)\s*(,?)$', stripped)
        if lua_match:
            key_part, quote, value, _, comma = lua_match.groups()
            if value.strip():
                prefix = f'{indent}{key_part}{quote}'
                suffix = f'{quote}{comma}'
                placeholders = self._extract_placeholders(value)
                return prefix, value, suffix, placeholders
        
        # === PO/POT формат: msgstr "text" ===
        po_match = re.match(r'^(msgstr\s+)(["\'])(.*)(\2)$', stripped)
        if po_match:
            prefix_part, quote, value, _ = po_match.groups()
            if value.strip():
                prefix = f'{indent}{prefix_part}{quote}'
                suffix = quote
                placeholders = self._extract_placeholders(value)
                return prefix, value, suffix, placeholders
        
        # === CSV формат (спрощено) - текст в лапках ===
        csv_match = re.match(r'^([^,]*,)(["\'])(.+)\2(,.*)$', stripped)
        if csv_match:
            before, quote, value, after = csv_match.groups()
            prefix = f'{indent}{before}{quote}'
            suffix = f'{quote}{after}'
            placeholders = self._extract_placeholders(value)
            return prefix, value, suffix, placeholders
        
        # === Якщо не знайшли формат - перекладаємо весь рядок якщо є текст ===
        # Перевіряємо чи містить кириличні або латинські літери (тобто текст)
        if re.search(r'[a-zA-Zа-яА-ЯіІїЇєЄґҐ]', stripped):
            placeholders = self._extract_placeholders(stripped)
            return indent, stripped, "", placeholders
        
        # Немає тексту для перекладу
        return indent, "", "", []
    
    def _extract_placeholders(self, text):
        """Витягує всі плейсхолдери/коди з тексту"""
        placeholders = []
        
        # Порядок важливий - спочатку більш специфічні патерни
        patterns = [
            r'\{\{[^}]+\}\}',              # {{name}}, {{variable}}
            r'\{[^}]+\}',                  # {0}, {name}, {variable}
            r'%\([^)]+\)[sdifx]',          # %(name)s
            r'%\d*\.?\d*[sdifxXeEgGcpb%]', # %s, %d, %2d, %.2f, %%
            r'\$\{[^}]+\}',                # ${variable}
            r'\$[a-zA-Z_][a-zA-Z0-9_]*',   # $variable
            r'<[^>]+>',                    # <tag>, <color=#FF0000>, </tag>
            r'\[[^\]]+\]',                 # [variable], [color]
            r'\\[nrtv\\"\'/]',             # \n, \t, \r, \\, \", \', \/
            r'&[a-zA-Z]+;',                # &nbsp;, &amp;
            r'&#x?[0-9a-fA-F]+;',          # &#123;, &#xAB;
            r'@[a-zA-Z_][a-zA-Z0-9_]*',    # @variable (деякі движки)
            r'#[a-zA-Z_][a-zA-Z0-9_]*#',   # #variable# (деякі движки)
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            placeholders.extend(matches)
        
        return placeholders
    
    def _restore_placeholders(self, original_text, translated_text, placeholders):
        """Відновлює плейсхолдери у перекладеному тексті"""
        if not placeholders:
            return translated_text
        
        result = translated_text
        
        # Знаходимо плейсхолдери в перекладі (можуть бути змінені/загублені)
        translated_placeholders = self._extract_placeholders(result)
        
        # Якщо всі плейсхолдери на місці та ідентичні - повертаємо як є
        if set(translated_placeholders) == set(placeholders):
            return result
        
        # Перевіряємо кожен плейсхолдер
        for placeholder in placeholders:
            if placeholder not in result:
                # Плейсхолдер зник - шукаємо схожий та замінюємо
                found_replacement = False
                for trans_ph in translated_placeholders:
                    # Якщо є щось схоже (напр. {0} став { 0 })
                    if trans_ph not in placeholders:
                        result = result.replace(trans_ph, placeholder, 1)
                        translated_placeholders.remove(trans_ph)
                        found_replacement = True
                        break
                
                # Якщо не знайшли заміну - додаємо в кінець
                if not found_replacement:
                    # Не додаємо теги в кінець, бо це зламає форматування
                    if not placeholder.startswith('<'):
                        result = result.rstrip() + ' ' + placeholder
        
        return result
    
    def _translate_line(self, line, model, placeholders=None, max_retries=3):
        """Переклад одного рядка з retry логікою та обробкою помилок контексту"""
        if placeholders is None:
            placeholders = []
        
        # Якщо рядок дуже довгий - розбиваємо на частини
        max_chars = 2000  # Безпечний ліміт для більшості моделей
        if len(line) > max_chars:
            return self._translate_long_line(line, model, max_chars)
        
        # Формуємо інформацію про плейсхолдери для промпту
        placeholder_info = ""
        if placeholders:
            placeholder_info = (
                f"\n\nУВАГА! У тексті є спеціальні коди/плейсхолдери, які ОБОВ'ЯЗКОВО треба зберегти БЕЗ ЗМІН: "
                f"{', '.join(set(placeholders))}"
            )
        
        system_prompt = (
            "You are a translator. Translate the text to Ukrainian. Output ONLY the translation, nothing else. "
            "No comments, no explanations, no 'I understand', no 'Ready to work' - ONLY the translated text."
            "\n\nRULES:"
            "\n- Keep all placeholders unchanged: {0}, {name}, %s, %d, $var, <tag>, [var], \\n"
            "\n- Use correct Ukrainian grammar: cases, genders, verb forms"
            "\n- Use natural Ukrainian: 'є' not 'являється', 'треба' not 'необхідно'"
            "\n- Gaming terms: quest→квест, skill→навичка, level→рівень, boss→бос"
            "\n- Names: Michael→Майкл, John→Джон, James→Джеймс"
            f"{placeholder_info}"
            "\n\nIMPORTANT: Your response must contain ONLY the Ukrainian translation. "
            "If you output anything other than the translation, you have failed."
        )
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Translate to Ukrainian: {line}"}
                    ],
                    temperature=0.3,
                    max_tokens=min(len(line) * 3 + 100, 4000)  # Обмежуємо max_tokens
                )
                result = response.choices[0].message.content.strip()
                
                # Перевірка на погані відповіді (LLM відповідає замість перекладу)
                bad_responses = [
                    "зрозуміло", "готовий до роботи", "надайте текст", "готовий перекладати",
                    "i understand", "ready to", "please provide", "i'm ready",
                    "вибачте", "не можу", "sorry", "i cannot", "i can't"
                ]
                result_lower = result.lower()
                for bad in bad_responses:
                    if bad in result_lower and len(result) > len(line) * 2:
                        # LLM відповів системним повідомленням - повертаємо оригінал
                        return line
                
                # Якщо відповідь занадто коротка або порожня
                if not result or len(result) < 2:
                    return line
                
                return result
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Перевіряємо на помилки контекстного вікна
                context_errors = [
                    "context_length_exceeded",
                    "context length",
                    "maximum context",
                    "token limit",
                    "too many tokens",
                    "max_tokens",
                    "context window",
                    "reduce the length",
                    "reduce your prompt"
                ]
                
                is_context_error = any(err in error_str for err in context_errors)
                
                if is_context_error:
                    # Спробуємо розбити рядок на менші частини
                    self.after(0, lambda: self._update_status(
                        f"⚠️ Рядок занадто довгий, розбиваємо...", 
                        self.colors["warning"]
                    ))
                    return self._translate_long_line(line, model, max_chars // 2)
                
                # Перевіряємо на rate limit
                rate_limit_errors = ["rate_limit", "rate limit", "too many requests", "429"]
                is_rate_limit = any(err in error_str for err in rate_limit_errors)
                
                if is_rate_limit:
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 секунд
                    self.after(0, lambda wt=wait_time: self._update_status(
                        f"⏳ Rate limit, очікування {wt}с...", 
                        self.colors["warning"]
                    ))
                    time.sleep(wait_time)
                    continue
                
                # Для інших помилок - експоненційна затримка
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt)  # 1, 2, 4 секунди
                    self.after(0, lambda wt=wait_time, att=attempt: self._update_status(
                        f"⚠️ Помилка, спроба {att + 2}/{max_retries} через {wt}с...", 
                        self.colors["warning"]
                    ))
                    time.sleep(wait_time)
                else:
                    # Остання спроба не вдалася - повертаємо оригінал з міткою
                    return f"[!] {line}"
        
        return line  # Fallback - повертаємо оригінал
    
    def _translate_long_line(self, line, model, chunk_size):
        """Переклад довгого рядка частинами"""
        # Розбиваємо по реченнях або словах
        chunks = self._split_into_chunks(line, chunk_size)
        translated_chunks = []
        
        for i, chunk in enumerate(chunks):
            if not self.is_translating:
                break
                
            self.after(0, lambda idx=i, total=len(chunks): self._update_status(
                f"📝 Довгий рядок: частина {idx + 1}/{total}...", 
                self.colors["warning"]
            ))
            
            # Перекладаємо кожну частину
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "Translate to Ukrainian. Output ONLY the translation, nothing else. "
                                "Keep placeholders: {0}, %s, <tag>, [var], $var, \\n unchanged."
                            )
                        },
                        {"role": "user", "content": chunk}
                    ],
                    temperature=0.3,
                    max_tokens=min(len(chunk) * 3, 2000)
                )
                translated_chunks.append(response.choices[0].message.content.strip())
            except Exception as e:
                # Якщо навіть частина не перекладається - копіюємо оригінал
                translated_chunks.append(chunk)
            
            # Невелика пауза між частинами
            time.sleep(0.3)
        
        return " ".join(translated_chunks)
    
    def _split_into_chunks(self, text, max_size):
        """Розбиття тексту на частини по реченнях"""
        # Спочатку спробуємо по реченнях
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_size:
                current_chunk += (" " if current_chunk else "") + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Якщо речення само по собі занадто довге - розбиваємо по словах
                if len(sentence) > max_size:
                    words = sentence.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk) + len(word) + 1 <= max_size:
                            current_chunk += (" " if current_chunk else "") + word
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = word
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]
    
    def _append_translated(self, text, line_idx):
        """Додавання перекладеного тексту"""
        if line_idx > 0:
            self.translated_text.insert("end", "\n")
        self.translated_text.insert("end", text)
        self.translated_text.see("end")
        
        # Оновлення лічильника
        self.translated_lines_label.configure(text=f"{line_idx + 1} рядків")
    
    def _update_progress(self, current, total):
        """Оновлення прогресу"""
        progress = (current + 1) / total
        self.progress_bar.set(progress)
        self.lines_label.configure(text=f"{current + 1} / {total} рядків")
        self._update_status(f"🔄 Переклад рядка {current + 1} з {total}...", self.colors["warning"])
        
        # Оновлення статистики швидкості
        self.translated_count = current + 1
        if self.translation_start_time and current > 0:
            elapsed = time.time() - self.translation_start_time
            lines_per_min = self.translated_count / (elapsed / 60) if elapsed > 0 else 0
            remaining = (total - current - 1) / lines_per_min if lines_per_min > 0 else 0
            self.speed_label.configure(
                text=f"⚡ {lines_per_min:.1f} р/хв | ⏳ ~{int(remaining)} хв залишилось"
            )
    
    def _update_status(self, text, color=None):
        """Оновлення статусу"""
        self.status_label.configure(text=text, text_color=color or self.colors["text_muted"])
    
    def _translation_complete(self):
        """Завершення перекладу"""
        self.is_translating = False
        self.translate_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.file_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        
        self.progress_bar.set(1)
        
        # Статистика
        if self.translation_start_time:
            elapsed = time.time() - self.translation_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            lines_per_min = self.translated_count / (elapsed / 60) if elapsed > 0 else 0
            self.speed_label.configure(
                text=f"⏱️ {minutes}:{seconds:02d} | 📊 {lines_per_min:.1f} рядків/хв"
            )
        
        self._update_status("✅ Переклад завершено!", self.colors["success"])
    
    def _stop_translation(self):
        """Зупинка перекладу"""
        self.is_translating = False
        self._update_status("⏹ Переклад зупинено", self.colors["warning"])
    
    def _save_translation(self):
        """Збереження перекладу"""
        if not self.translated_lines:
            messagebox.showwarning("Увага", "Немає що зберігати!")
            return
        
        # Генерація імені файлу з -ukr
        original_path = Path(self.file_path)
        original_ext = original_path.suffix.lower()
        new_name = f"{original_path.stem}-ukr{original_path.suffix}"
        
        # Визначаємо тип файлу для фільтра
        ext_names = {
            ".json": "JSON",
            ".xml": "XML", 
            ".txt": "Текстовий файл",
            ".ini": "INI файл",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".lua": "Lua",
            ".csv": "CSV",
            ".po": "PO (Gettext)",
            ".pot": "POT (Gettext)",
            ".srt": "Субтитри SRT",
            ".lang": "Language файл",
            ".properties": "Properties"
        }
        
        # Створюємо список типів з оригінальним розширенням першим
        filetypes = []
        if original_ext in ext_names:
            filetypes.append((f"{ext_names[original_ext]} (*{original_ext})", f"*{original_ext}"))
        filetypes.append(("Всі файли", "*.*"))
        
        # Діалог збереження
        save_path = filedialog.asksaveasfilename(
            initialdir=original_path.parent,
            initialfile=new_name,
            defaultextension=original_path.suffix,
            filetypes=filetypes
        )
        
        if save_path:
            try:
                content = "\n".join(self.translated_lines)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                self._update_status(f"💾 Збережено: {Path(save_path).name}", self.colors["success"])
                messagebox.showinfo("Успіх", f"Файл збережено:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося зберегти файл:\n{str(e)}")
    
    def _export_translation(self):
        """Експорт перекладу в різні формати"""
        if not self.translated_lines:
            messagebox.showwarning("Увага", "Немає що експортувати!")
            return
        
        # Діалог вибору формату
        export_dialog = ctk.CTkToplevel(self)
        export_dialog.title("📤 Експорт перекладу")
        export_dialog.geometry("450x400")
        export_dialog.configure(fg_color=self.colors["bg_dark"])
        export_dialog.transient(self)
        export_dialog.grab_set()
        set_dark_title_bar(export_dialog)
        
        ctk.CTkLabel(
            export_dialog, text="📤 Виберіть формат експорту",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text"]
        ).pack(pady=(25, 20))
        
        formats_frame = ctk.CTkFrame(export_dialog, fg_color=self.colors["bg_card"], corner_radius=10)
        formats_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        export_formats = [
            ("📄 Тільки переклад (.txt)", "txt_only", "Тільки перекладений текст"),
            ("📊 Side-by-Side (.txt)", "side_by_side", "Оригінал | Переклад"),
            ("📋 TSV таблиця (.tsv)", "tsv", "Для імпорту в Excel"),
            ("🔄 JSON (.json)", "json", "Структурований формат"),
            ("📝 HTML (.html)", "html", "Для перегляду в браузері"),
        ]
        
        selected_format = ctk.StringVar(value="txt_only")
        
        for text, value, desc in export_formats:
            frame = ctk.CTkFrame(formats_frame, fg_color="transparent")
            frame.pack(fill="x", padx=15, pady=8)
            
            ctk.CTkRadioButton(
                frame, text=text, value=value, variable=selected_format,
                font=ctk.CTkFont(size=13),
                text_color=self.colors["text"],
                fg_color=self.colors["accent"],
                hover_color=self.colors["accent_hover"]
            ).pack(side="left")
            
            ctk.CTkLabel(
                frame, text=f"— {desc}",
                font=ctk.CTkFont(size=11),
                text_color=self.colors["text_muted"]
            ).pack(side="left", padx=(10, 0))
        
        def do_export():
            fmt = selected_format.get()
            export_dialog.destroy()
            self._do_export(fmt)
        
        btn_frame = ctk.CTkFrame(export_dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(0, 25))
        
        ctk.CTkButton(btn_frame, text="📤 Експортувати", width=140, height=40,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=self.colors["success"], hover_color="#2ea043",
                      command=do_export).pack(side="left", padx=(0, 15))
        
        ctk.CTkButton(btn_frame, text="Скасувати", width=100, height=40,
                      fg_color=self.colors["bg_input"], hover_color=self.colors["border"],
                      command=export_dialog.destroy).pack(side="left")
    
    def _do_export(self, format_type):
        """Виконати експорт у вибраному форматі"""
        original_path = Path(self.file_path)
        
        extensions = {
            "txt_only": ".txt",
            "side_by_side": ".txt", 
            "tsv": ".tsv",
            "json": ".json",
            "html": ".html"
        }
        
        ext = extensions.get(format_type, ".txt")
        default_name = f"{original_path.stem}-ukr-export{ext}"
        
        save_path = filedialog.asksaveasfilename(
            initialdir=original_path.parent,
            initialfile=default_name,
            defaultextension=ext,
            filetypes=[("Всі файли", "*.*")]
        )
        
        if not save_path:
            return
        
        try:
            if format_type == "txt_only":
                content = "\n".join(self.translated_lines)
            
            elif format_type == "side_by_side":
                lines = []
                max_len = max(len(line) for line in self.original_lines) + 5
                for orig, trans in zip(self.original_lines, self.translated_lines):
                    lines.append(f"{orig:<{max_len}} │ {trans}")
                content = "\n".join(lines)
            
            elif format_type == "tsv":
                lines = ["Original\tTranslation"]
                for orig, trans in zip(self.original_lines, self.translated_lines):
                    # Екрануємо таби
                    orig_clean = orig.replace("\t", "    ")
                    trans_clean = trans.replace("\t", "    ")
                    lines.append(f"{orig_clean}\t{trans_clean}")
                content = "\n".join(lines)
            
            elif format_type == "json":
                data = {
                    "source_file": str(original_path),
                    "lines": [
                        {"original": orig, "translation": trans}
                        for orig, trans in zip(self.original_lines, self.translated_lines)
                    ]
                }
                content = json.dumps(data, ensure_ascii=False, indent=2)
            
            elif format_type == "html":
                rows = ""
                for i, (orig, trans) in enumerate(zip(self.original_lines, self.translated_lines)):
                    orig_html = orig.replace("<", "&lt;").replace(">", "&gt;")
                    trans_html = trans.replace("<", "&lt;").replace(">", "&gt;")
                    rows += f"""
                    <tr>
                        <td style="color:#888">{i+1}</td>
                        <td>{orig_html}</td>
                        <td style="color:#ffd700">{trans_html}</td>
                    </tr>"""
                
                content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Переклад - {original_path.name}</title>
    <style>
        body {{ background: #0d1117; color: #c9d1d9; font-family: 'Consolas', monospace; padding: 20px; }}
        h1 {{ color: #ffd700; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #161b22; padding: 12px; text-align: left; border-bottom: 2px solid #30363d; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid #21262d; vertical-align: top; }}
        tr:hover {{ background: #161b22; }}
        .flag {{ display: inline-block; }}
        .blue {{ background: #0057b7; width: 30px; height: 15px; }}
        .yellow {{ background: #ffd700; width: 30px; height: 15px; }}
    </style>
</head>
<body>
    <h1>🇺🇦 TranslatorUKR - Експорт</h1>
    <p>Файл: {original_path.name}</p>
    <table>
        <tr>
            <th>#</th>
            <th>Оригінал</th>
            <th>🇺🇦 Переклад</th>
        </tr>
        {rows}
    </table>
</body>
</html>"""
            
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self._update_status(f"📤 Експортовано: {Path(save_path).name}", self.colors["success"])
            messagebox.showinfo("Успіх", f"Файл експортовано:\n{save_path}")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося експортувати:\n{str(e)}")
    
    # ============ ПОШУК ============
    
    def _search_text(self):
        """Пошук тексту в оригіналі та перекладі"""
        query = self.search_entry.get().strip().lower()
        if not query:
            return
        
        self.search_matches = []
        self.current_match = 0
        
        # Пошук в оригіналі
        original_content = self.original_text.get("1.0", "end")
        translated_content = self.translated_text.get("1.0", "end")
        
        # Очистити попередні виділення
        self.original_text.tag_remove("search", "1.0", "end")
        self.translated_text.tag_remove("search", "1.0", "end")
        
        # Налаштувати теги
        self.original_text.tag_config("search", background="#ffd700", foreground="#000000")
        self.translated_text.tag_config("search", background="#ffd700", foreground="#000000")
        
        # Шукати в оригіналі
        start = "1.0"
        while True:
            pos = self.original_text.search(query, start, nocase=True, stopindex="end")
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.original_text.tag_add("search", pos, end)
            self.search_matches.append(("original", pos))
            start = end
        
        # Шукати в перекладі
        start = "1.0"
        while True:
            pos = self.translated_text.search(query, start, nocase=True, stopindex="end")
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.translated_text.tag_add("search", pos, end)
            self.search_matches.append(("translated", pos))
            start = end
        
        if self.search_matches:
            self.search_result_label.configure(
                text=f"Знайдено: {len(self.search_matches)}",
                text_color=self.colors["success"]
            )
            self._goto_match(0)
        else:
            self.search_result_label.configure(
                text="Не знайдено",
                text_color=self.colors["warning"]
            )
    
    def _search_next(self):
        """Перейти до наступного збігу"""
        if self.search_matches:
            self.current_match = (self.current_match + 1) % len(self.search_matches)
            self._goto_match(self.current_match)
    
    def _search_prev(self):
        """Перейти до попереднього збігу"""
        if self.search_matches:
            self.current_match = (self.current_match - 1) % len(self.search_matches)
            self._goto_match(self.current_match)
    
    def _goto_match(self, index):
        """Перейти до збігу за індексом"""
        if not self.search_matches:
            return
        
        source, pos = self.search_matches[index]
        if source == "original":
            self.original_text.see(pos)
            self.original_text.mark_set("insert", pos)
        else:
            self.translated_text.see(pos)
            self.translated_text.mark_set("insert", pos)
        
        self.search_result_label.configure(
            text=f"{index + 1} / {len(self.search_matches)}"
        )
    
    # ============ ГЛОСАРІЙ ============
    
    def _load_glossary(self):
        """Завантаження глосарію з файлу"""
        glossary_file = Path("glossary.json")
        if glossary_file.exists():
            try:
                with open(glossary_file, "r", encoding="utf-8") as f:
                    self.glossary = json.load(f)
            except:
                self.glossary = {}
        else:
            # Базовий глосарій ігрових термінів
            self.glossary = {
                "quest": "квест",
                "skill": "навичка",
                "level": "рівень",
                "boss": "бос",
                "health": "здоров'я",
                "mana": "мана",
                "stamina": "витривалість",
                "experience": "досвід",
                "inventory": "інвентар",
                "armor": "броня",
                "weapon": "зброя",
                "spell": "закляття",
                "dungeon": "підземелля",
                "loot": "здобич",
                "NPC": "НПС",
                "respawn": "відродження",
                "save": "збереження",
                "load": "завантаження",
                "settings": "налаштування",
                "pause": "пауза",
                "resume": "продовжити",
                "exit": "вийти",
                "start": "почати",
                "continue": "продовжити"
            }
            self._save_glossary()
    
    def _save_glossary(self):
        """Збереження глосарію"""
        with open("glossary.json", "w", encoding="utf-8") as f:
            json.dump(self.glossary, f, ensure_ascii=False, indent=2)
    
    def _open_glossary_editor(self):
        """Відкриття редактора глосарію"""
        editor = ctk.CTkToplevel(self)
        editor.title("📚 Редактор глосарію")
        editor.geometry("600x500")
        editor.configure(fg_color=self.colors["bg_dark"])
        editor.transient(self)
        editor.grab_set()
        set_dark_title_bar(editor)
        
        # Заголовок
        ctk.CTkLabel(
            editor, text="📚 Глосарій термінів",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text"]
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            editor, text="Додайте власні переклади термінів для локалізації",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"]
        ).pack(pady=(0, 15))
        
        # Форма додавання
        add_frame = ctk.CTkFrame(editor, fg_color=self.colors["bg_card"], corner_radius=10)
        add_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        add_inner = ctk.CTkFrame(add_frame, fg_color="transparent")
        add_inner.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(add_inner, text="Оригінал:", font=ctk.CTkFont(size=12),
                     text_color=self.colors["text"]).pack(side="left")
        
        orig_entry = ctk.CTkEntry(add_inner, width=150, height=32,
                                   fg_color=self.colors["bg_input"],
                                   border_color=self.colors["border"])
        orig_entry.pack(side="left", padx=(10, 20))
        
        ctk.CTkLabel(add_inner, text="Переклад:", font=ctk.CTkFont(size=12),
                     text_color=self.colors["text"]).pack(side="left")
        
        trans_entry = ctk.CTkEntry(add_inner, width=150, height=32,
                                    fg_color=self.colors["bg_input"],
                                    border_color=self.colors["border"])
        trans_entry.pack(side="left", padx=(10, 20))
        
        def add_term():
            orig = orig_entry.get().strip()
            trans = trans_entry.get().strip()
            if orig and trans:
                self.glossary[orig] = trans
                self._save_glossary()
                refresh_list()
                orig_entry.delete(0, "end")
                trans_entry.delete(0, "end")
        
        ctk.CTkButton(add_inner, text="➕ Додати", width=100, height=32,
                      fg_color=self.colors["success"], hover_color="#2ea043",
                      command=add_term).pack(side="left")
        
        # Список термінів
        list_frame = ctk.CTkScrollableFrame(editor, fg_color=self.colors["bg_card"],
                                             corner_radius=10, height=280)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        def refresh_list():
            for widget in list_frame.winfo_children():
                widget.destroy()
            
            for orig, trans in sorted(self.glossary.items()):
                item_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
                item_frame.pack(fill="x", pady=2)
                
                ctk.CTkLabel(item_frame, text=orig, width=200,
                             font=ctk.CTkFont(size=12),
                             text_color=self.colors["text"],
                             anchor="w").pack(side="left", padx=(10, 0))
                
                ctk.CTkLabel(item_frame, text="→",
                             font=ctk.CTkFont(size=12),
                             text_color=self.colors["text_muted"]).pack(side="left", padx=10)
                
                ctk.CTkLabel(item_frame, text=trans, width=200,
                             font=ctk.CTkFont(size=12),
                             text_color=self.colors["ukr_yellow"],
                             anchor="w").pack(side="left")
                
                def delete_term(o=orig):
                    del self.glossary[o]
                    self._save_glossary()
                    refresh_list()
                
                ctk.CTkButton(item_frame, text="🗑️", width=30, height=25,
                              fg_color="transparent", hover_color="#da3633",
                              command=delete_term).pack(side="right", padx=10)
        
        refresh_list()
        
        # Кнопка закриття
        ctk.CTkButton(editor, text="Закрити", width=120, height=35,
                      fg_color=self.colors["bg_input"], hover_color=self.colors["border"],
                      command=editor.destroy).pack(pady=(0, 20))
    
    # ============ ГАРЯЧІ КЛАВІШІ ============
    
    def _setup_hotkeys(self):
        """Налаштування гарячих клавіш"""
        self.bind("<Control-o>", lambda e: self._select_file())
        self.bind("<Control-O>", lambda e: self._select_file())
        self.bind("<Control-s>", lambda e: self._save_translation())
        self.bind("<Control-S>", lambda e: self._save_translation())
        self.bind("<Control-t>", lambda e: self._start_translation())
        self.bind("<Control-T>", lambda e: self._start_translation())
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<Control-F>", lambda e: self._focus_search())
        self.bind("<Control-q>", lambda e: self._check_translation_quality())
        self.bind("<Control-Q>", lambda e: self._check_translation_quality())
        self.bind("<Control-g>", lambda e: self._open_games_window())
        self.bind("<Control-G>", lambda e: self._open_games_window())
        self.bind("<Control-g>", lambda e: self._open_glossary_editor())
        self.bind("<Control-G>", lambda e: self._open_glossary_editor())
        self.bind("<Escape>", lambda e: self._stop_translation())
        self.bind("<F3>", lambda e: self._search_next())
        self.bind("<Shift-F3>", lambda e: self._search_prev())
        self.bind("<F5>", lambda e: self._start_translation())
        self.bind("<F12>", lambda e: self._show_hotkeys_help())
    
    def _focus_search(self):
        """Фокус на поле пошуку"""
        self.search_entry.focus_set()
    
    def _show_hotkeys_help(self):
        """Показати довідку про програму"""
        help_window = ctk.CTkToplevel(self)
        help_window.title("ℹ️ Про програму")
        help_window.geometry("900x620")
        help_window.configure(fg_color=self.colors["bg_dark"])
        help_window.transient(self)
        help_window.grab_set()
        set_dark_title_bar(help_window)
        
        # Scrollable frame для всього контенту
        scroll_frame = ctk.CTkScrollableFrame(help_window, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === ЗАГОЛОВОК ===
        ctk.CTkLabel(
            scroll_frame, text="🇺🇦 TranslatorUKR 1.0",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.colors["ukr_yellow"]
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            scroll_frame, text="Професійний перекладач файлів на українську мову",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_muted"]
        ).pack(pady=(0, 20))
        
        # === ПРО ПРОГРАМУ ===
        about_frame = ctk.CTkFrame(scroll_frame, fg_color=self.colors["bg_card"], corner_radius=12)
        about_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            about_frame, text="📖 Про програму",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        about_text = """TranslatorUKR — це інструмент для полегшення та пришвидшення перекладів на українську мову.

⚠️ ВАЖЛИВО: Автор цієї програми ПОПЕРЕДЖУЄ, що ШІ переклад не є якісним і найкраще застосування цієї програми — це автоматичний переклад, а потім ручне редагування тексту!

Автор ЗАКЛИКАЄ використовувати автоматичний переклад ТІЛЬКИ як фундамент для подальшої редакції власноруч!

Програма підходить для:
• Локалізації відеоігор (JSON, XML, Lua, YAML, PO та інші формати)
• Перекладу субтитрів (SRT)
• Перекладу документації та текстових файлів
• Будь-яких файлів локалізації

Особливості програми:
• Підтримка хмарних API (OpenAI, DeepSeek, Anthropic, Groq тощо)
• Підтримка локальних LLM (LM Studio, Ollama, GPT4All тощо)
• Збереження структури файлу — код та теги не перекладаються
• Глосарій для послідовного перекладу термінів
• Міні-ігри для очікування (Змійка, Понг, Flappy Bird)"""
        
        ctk.CTkLabel(
            about_frame, text=about_text,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text"],
            justify="left",
            wraplength=720
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # === ІНСТРУКЦІЯ ===
        guide_frame = ctk.CTkFrame(scroll_frame, fg_color=self.colors["bg_card"], corner_radius=12)
        guide_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            guide_frame, text="📋 Інструкція з використання",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        guide_text = """КРОК 1: Налаштування LLM

Для хмарних API (наприклад, DeepSeek):
1. Виберіть провайдера зі списку (наприклад, "DeepSeek")
2. Введіть ваш API ключ у відповідне поле
3. Виберіть модель зі списку або введіть власну назву моделі

Для локальних LLM (наприклад, LM Studio):
1. Завантажте та встановіть LM Studio (lmstudio.ai)
2. Завантажте модель, наприклад: mamaylm-gemma-3-12b-it-v1.0@q8_0
3. Запустіть локальний сервер у LM Studio (вкладка "Local Server")
4. У програмі виберіть провайдера "LM Studio (Local)"
5. Base URL залиште за замовчуванням: http://localhost:1234/v1
6. API ключ можна залишити порожнім або написати "lm-studio"
7. У полі "Своя модель" введіть: mamaylm-gemma-3-12b-it-v1.0@q8_0

КРОК 2: Вибір файлу
1. Натисніть кнопку "📂 Вибрати файл"
2. Виберіть файл для перекладу (підтримуються всі текстові формати)
3. Оригінальний текст з'явиться в лівій панелі

КРОК 3: Налаштування глосарію (опціонально)
1. Натисніть "📚 Глосарій" для відкриття редактора термінів
2. Додайте терміни, які мають перекладатися однаково
3. Наприклад: "Health" → "Здоров'я", "Mana" → "Мана"

КРОК 4: Переклад
1. Натисніть "🚀 Почати переклад"
2. Спостерігайте за прогресом у реальному часі
3. Переклад з'являтиметься в правій панелі
4. Під час очікування можете пограти в міні-ігри (кнопка "🎮 Ігри")

КРОК 5: Редагування та збереження
1. Після завершення перегляньте переклад
2. Натисніть "✏️ Редагувати" для внесення правок вручну
3. Використовуйте пошук (Ctrl+F) для знаходження тексту
4. Натисніть "💾 Зберегти переклад" для збереження файлу
5. Файл збережеться з суфіксом "-ukr" (наприклад: game-ukr.json)

ПОРАДИ:
• Для великих файлів використовуйте потужніші моделі
• Локальні LLM працюють без інтернету та безкоштовно
• Глосарій допомагає зберегти консистентність термінів
• Автозбереження зберігає прогрес кожні 30 секунд"""
        
        ctk.CTkLabel(
            guide_frame, text=guide_text,
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text"],
            justify="left",
            wraplength=720
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # === АВТОР ===
        author_frame = ctk.CTkFrame(scroll_frame, fg_color=self.colors["bg_card"], corner_radius=12)
        author_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            author_frame, text="👨‍💻 Автор",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            author_frame, text="Програму розробив Відлюдник",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["ukr_blue"]
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            author_frame, 
            text="Якщо програма вам сподобалась і ви хочете підтримати розробку,\nможете подякувати на картку:",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text"],
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        card_frame = ctk.CTkFrame(author_frame, fg_color=self.colors["bg_input"], corner_radius=8)
        card_frame.pack(anchor="w", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            card_frame, text="💳  4441 1111 3424 9402",
            font=ctk.CTkFont(size=18, weight="bold", family="Consolas"),
            text_color=self.colors["ukr_yellow"]
        ).pack(padx=20, pady=12)
        
        ctk.CTkLabel(
            author_frame, 
            text="Дякую за використання TranslatorUKR! 🇺🇦",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_muted"]
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Кнопка закриття
        ctk.CTkButton(scroll_frame, text="Закрити", width=150, height=40,
                      font=ctk.CTkFont(size=14),
                      fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
                      command=help_window.destroy).pack(pady=(10, 0))
    
    # ============ КОПІЮВАННЯ ============
    
    def _copy_to_clipboard(self, source):
        """Копіювання тексту в буфер обміну"""
        if source == "original":
            text = self.original_text.get("1.0", "end-1c")
        else:
            text = self.translated_text.get("1.0", "end-1c")
        
        self.clipboard_clear()
        self.clipboard_append(text)
        self._update_status(f"📋 Скопійовано в буфер обміну!", self.colors["success"])
    
    # ============ РЕДАГУВАННЯ ============
    
    def _toggle_edit_mode(self):
        """Перемикання режиму редагування перекладу"""
        current_state = self.translated_text.cget("state")
        if current_state == "normal":
            self.translated_text.configure(state="disabled")
            self.edit_btn.configure(text="✏️ Редагувати", fg_color="transparent")
            self._update_status("🔒 Редагування вимкнено", self.colors["text_muted"])
            # Оновлюємо translated_lines з текстового поля
            self.translated_lines = self.translated_text.get("1.0", "end-1c").split("\n")
        else:
            self.translated_text.configure(state="normal")
            self.edit_btn.configure(text="💾 Зберегти", fg_color="#2ea043")
            self._update_status("✏️ Режим редагування. Редагуйте переклад вручну!", self.colors["warning"])
    
    # ============ ПЕРЕВІРКА ЯКОСТІ ============
    
    def _check_translation_quality(self):
        """Перевірка якості перекладу"""
        if not self.translated_lines or all(not line for line in self.translated_lines):
            self._update_status("⚠️ Немає перекладу для перевірки", self.colors["warning"])
            return
        
        issues = []
        
        for i, (orig, trans) in enumerate(zip(self.original_lines, self.translated_lines)):
            if not trans.strip() and orig.strip():
                issues.append(f"Рядок {i+1}: порожній переклад")
                continue
            
            # Перевірка плейсхолдерів
            orig_placeholders = set(self._extract_placeholders(orig))
            trans_placeholders = set(self._extract_placeholders(trans))
            
            missing = orig_placeholders - trans_placeholders
            if missing:
                issues.append(f"Рядок {i+1}: відсутні плейсхолдери: {', '.join(missing)}")
        
        # Показати результати
        if issues:
            self._show_quality_report(issues)
        else:
            self._update_status("✅ Перевірка пройдена! Всі плейсхолдери на місці", self.colors["success"])
    
    def _show_quality_report(self, issues):
        """Показати звіт про якість"""
        report = ctk.CTkToplevel(self)
        report.title("⚠️ Звіт про якість перекладу")
        report.geometry("600x450")
        report.configure(fg_color=self.colors["bg_dark"])
        report.transient(self)
        report.grab_set()
        set_dark_title_bar(report)
        
        # Заголовок
        ctk.CTkLabel(
            report, text=f"⚠️ Знайдено {len(issues)} проблем",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["warning"]
        ).pack(pady=(20, 15))
        
        # Список проблем
        list_frame = ctk.CTkScrollableFrame(report, fg_color=self.colors["bg_card"],
                                             corner_radius=10, height=300)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        for issue in issues[:50]:  # Максимум 50 проблем
            ctk.CTkLabel(
                list_frame, text=f"• {issue}",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text"],
                anchor="w"
            ).pack(fill="x", padx=10, pady=3)
        
        if len(issues) > 50:
            ctk.CTkLabel(
                list_frame, text=f"... та ще {len(issues) - 50} проблем",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_muted"]
            ).pack(padx=10, pady=5)
        
        ctk.CTkButton(report, text="Закрити", width=120, height=35,
                      fg_color=self.colors["bg_input"], hover_color=self.colors["border"],
                      command=report.destroy).pack(pady=(0, 20))
    
    # ============ BATCH ПЕРЕКЛАД ============
    
    def _open_games_window(self):
        """Вікно з міні-іграми для очікування перекладу"""
        if self.games_window is not None and self.games_window.winfo_exists():
            self.games_window.lift()
            self.games_window.focus_force()
            return
        
        self.games_window = ctk.CTkToplevel(self)
        self.games_window.title("🎮 Міні-ігри")
        self.games_window.geometry("420x520")
        self.games_window.configure(fg_color=self.colors["bg_dark"])
        self.games_window.attributes("-topmost", True)
        self.games_window.resizable(False, False)
        set_dark_title_bar(self.games_window)
        
        # Заголовок
        header = ctk.CTkFrame(self.games_window, fg_color=self.colors["bg_card"], corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(
            header, text="🎮 Вбий час поки переклад робиться!",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        ).pack(pady=15)
        
        # Tabview для ігор
        tabview = ctk.CTkTabview(
            self.games_window, 
            fg_color=self.colors["bg_card"],
            segmented_button_fg_color=self.colors["bg_input"],
            segmented_button_selected_color=self.colors["accent"],
            segmented_button_selected_hover_color=self.colors["accent_hover"]
        )
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_snake = tabview.add("🐍 Змійка")
        tab_pong = tabview.add("🏓 Понг")
        tab_flappy = tabview.add("🐤 Flappy")
        
        # ============ ЗМІЙКА ============
        self._create_snake_game(tab_snake)
        
        # ============ ПОНГ ============
        self._create_pong_game(tab_pong)
        
        # ============ FLAPPY BIRD ============
        self._create_flappy_game(tab_flappy)
    
    def _create_snake_game(self, parent):
        """Гра Змійка"""
        import random
        
        game_frame = ctk.CTkFrame(parent, fg_color="transparent")
        game_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(game_frame, width=380, height=380, bg="#0d1117", highlightthickness=2, highlightbackground="#30363d")
        canvas.pack(pady=5)
        
        cell_size = 20
        grid_width = 19
        grid_height = 19
        
        snake_state = {
            "snake": [(9, 9), (8, 9), (7, 9)],
            "direction": "Right",
            "food": (15, 9),
            "score": 0,
            "running": False,
            "game_over": False
        }
        
        score_label = ctk.CTkLabel(game_frame, text="Рахунок: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["ukr_yellow"])
        score_label.pack(pady=5)
        
        def draw():
            canvas.delete("all")
            # Їжа
            fx, fy = snake_state["food"]
            canvas.create_oval(fx*cell_size+2, fy*cell_size+2, (fx+1)*cell_size-2, (fy+1)*cell_size-2, fill="#da3633", outline="#ff6b6b")
            # Змійка
            for i, (x, y) in enumerate(snake_state["snake"]):
                color = "#238636" if i == 0 else "#2ea043"
                canvas.create_rectangle(x*cell_size+1, y*cell_size+1, (x+1)*cell_size-1, (y+1)*cell_size-1, fill=color, outline="#3fb950")
        
        def move():
            if not snake_state["running"] or snake_state["game_over"]:
                return
            
            head = snake_state["snake"][0]
            d = snake_state["direction"]
            if d == "Up": new_head = (head[0], head[1]-1)
            elif d == "Down": new_head = (head[0], head[1]+1)
            elif d == "Left": new_head = (head[0]-1, head[1])
            else: new_head = (head[0]+1, head[1])
            
            # Перевірка зіткнення
            if (new_head[0] < 0 or new_head[0] >= grid_width or 
                new_head[1] < 0 or new_head[1] >= grid_height or
                new_head in snake_state["snake"]):
                snake_state["game_over"] = True
                snake_state["running"] = False
                canvas.create_text(190, 190, text="GAME OVER", fill="#da3633", font=("Arial", 20, "bold"))
                start_btn.configure(text="🔄 Заново")
                return
            
            snake_state["snake"].insert(0, new_head)
            
            if new_head == snake_state["food"]:
                snake_state["score"] += 10
                score_label.configure(text=f"Рахунок: {snake_state['score']}")
                while True:
                    new_food = (random.randint(0, grid_width-1), random.randint(0, grid_height-1))
                    if new_food not in snake_state["snake"]:
                        snake_state["food"] = new_food
                        break
            else:
                snake_state["snake"].pop()
            
            draw()
            if snake_state["running"]:
                canvas.after(100, move)
        
        def on_key(event):
            key = event.keysym
            opp = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
            if key in opp and key != opp.get(snake_state["direction"]):
                snake_state["direction"] = key
        
        def start_game():
            snake_state["snake"] = [(9, 9), (8, 9), (7, 9)]
            snake_state["direction"] = "Right"
            snake_state["food"] = (15, 9)
            snake_state["score"] = 0
            snake_state["game_over"] = False
            snake_state["running"] = True
            score_label.configure(text="Рахунок: 0")
            start_btn.configure(text="⏸️ Пауза")
            canvas.focus_set()
            draw()
            move()
        
        def toggle_game():
            if snake_state["game_over"]:
                start_game()
            elif snake_state["running"]:
                snake_state["running"] = False
                start_btn.configure(text="▶️ Продовжити")
            else:
                snake_state["running"] = True
                start_btn.configure(text="⏸️ Пауза")
                move()
        
        canvas.bind("<Key>", on_key)
        canvas.bind("<Up>", on_key)
        canvas.bind("<Down>", on_key)
        canvas.bind("<Left>", on_key)
        canvas.bind("<Right>", on_key)
        
        start_btn = ctk.CTkButton(game_frame, text="▶️ Старт", width=120, height=35, fg_color=self.colors["success"], hover_color="#2ea043", command=toggle_game)
        start_btn.pack(pady=5)
        
        draw()
    
    def _create_pong_game(self, parent):
        """Гра Понг"""
        game_frame = ctk.CTkFrame(parent, fg_color="transparent")
        game_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(game_frame, width=380, height=300, bg="#0d1117", highlightthickness=2, highlightbackground="#30363d")
        canvas.pack(pady=5)
        
        pong_state = {
            "paddle_y": 130,
            "ball_x": 190, "ball_y": 150,
            "ball_dx": 4, "ball_dy": 3,
            "score": 0,
            "running": False
        }
        
        paddle_height = 60
        paddle_width = 10
        ball_size = 12
        
        score_label = ctk.CTkLabel(game_frame, text="Рахунок: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["ukr_yellow"])
        score_label.pack(pady=5)
        
        def draw():
            canvas.delete("all")
            # Paddle
            canvas.create_rectangle(10, pong_state["paddle_y"], 10+paddle_width, pong_state["paddle_y"]+paddle_height, fill="#0066ff", outline="#58a6ff")
            # AI Paddle
            ai_y = pong_state["ball_y"] - paddle_height//2
            ai_y = max(0, min(300-paddle_height, ai_y))
            canvas.create_rectangle(360, ai_y, 370, ai_y+paddle_height, fill="#da3633", outline="#ff6b6b")
            # Ball
            canvas.create_oval(pong_state["ball_x"]-ball_size//2, pong_state["ball_y"]-ball_size//2, pong_state["ball_x"]+ball_size//2, pong_state["ball_y"]+ball_size//2, fill="#ffd33d", outline="#f0e68c")
            # Center line
            for i in range(0, 300, 20):
                canvas.create_line(190, i, 190, i+10, fill="#30363d", width=2)
        
        def update():
            if not pong_state["running"]:
                return
            
            pong_state["ball_x"] += pong_state["ball_dx"]
            pong_state["ball_y"] += pong_state["ball_dy"]
            
            # Відбиття від стін
            if pong_state["ball_y"] <= ball_size//2 or pong_state["ball_y"] >= 300-ball_size//2:
                pong_state["ball_dy"] *= -1
            
            # Відбиття від paddle гравця
            if (pong_state["ball_x"] <= 20+ball_size//2 and 
                pong_state["paddle_y"] <= pong_state["ball_y"] <= pong_state["paddle_y"]+paddle_height):
                pong_state["ball_dx"] = abs(pong_state["ball_dx"])
                pong_state["score"] += 1
                score_label.configure(text=f"Рахунок: {pong_state['score']}")
            
            # Відбиття від AI paddle
            ai_y = pong_state["ball_y"] - paddle_height//2
            ai_y = max(0, min(300-paddle_height, ai_y))
            if (pong_state["ball_x"] >= 350-ball_size//2 and ai_y <= pong_state["ball_y"] <= ai_y+paddle_height):
                pong_state["ball_dx"] = -abs(pong_state["ball_dx"])
            
            # Програш
            if pong_state["ball_x"] <= 0:
                pong_state["running"] = False
                canvas.create_text(190, 150, text="GAME OVER", fill="#da3633", font=("Arial", 20, "bold"))
                start_btn.configure(text="🔄 Заново")
                return
            
            # М'яч вийшов справа - переможець
            if pong_state["ball_x"] >= 380:
                pong_state["ball_x"] = 190
                pong_state["ball_y"] = 150
                pong_state["ball_dx"] = -4
                pong_state["score"] += 5
                score_label.configure(text=f"Рахунок: {pong_state['score']}")
            
            draw()
            canvas.after(30, update)
        
        def on_motion(event):
            pong_state["paddle_y"] = max(0, min(300-paddle_height, event.y - paddle_height//2))
            if not pong_state["running"]:
                draw()
        
        def start_game():
            pong_state["paddle_y"] = 130
            pong_state["ball_x"] = 190
            pong_state["ball_y"] = 150
            pong_state["ball_dx"] = 4
            pong_state["ball_dy"] = 3
            pong_state["score"] = 0
            pong_state["running"] = True
            score_label.configure(text="Рахунок: 0")
            start_btn.configure(text="⏸️ Пауза")
            update()
        
        def toggle_game():
            if not pong_state["running"] and pong_state["ball_x"] <= 0:
                start_game()
            elif pong_state["running"]:
                pong_state["running"] = False
                start_btn.configure(text="▶️ Продовжити")
            else:
                pong_state["running"] = True
                start_btn.configure(text="⏸️ Пауза")
                update()
        
        canvas.bind("<Motion>", on_motion)
        
        start_btn = ctk.CTkButton(game_frame, text="▶️ Старт", width=120, height=35, fg_color=self.colors["success"], hover_color="#2ea043", command=toggle_game)
        start_btn.pack(pady=5)
        
        draw()
    
    def _create_flappy_game(self, parent):
        """Гра Flappy Bird"""
        import random
        
        game_frame = ctk.CTkFrame(parent, fg_color="transparent")
        game_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(game_frame, width=380, height=380, bg="#1a1a2e", highlightthickness=2, highlightbackground="#30363d")
        canvas.pack(pady=5)
        
        # Параметри гри
        bird_x = 80
        bird_size = 20
        pipe_width = 50
        pipe_gap = 120
        gravity = 0.6
        jump_strength = -9
        pipe_speed = 4
        
        flappy_state = {
            "bird_y": 190,
            "velocity": 0,
            "pipes": [],
            "score": 0,
            "running": False,
            "game_over": False,
            "best_score": 0
        }
        
        score_label = ctk.CTkLabel(game_frame, text="Рахунок: 0 | Рекорд: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["ukr_yellow"])
        score_label.pack(pady=5)
        
        def spawn_pipe():
            gap_y = random.randint(80, 260)
            flappy_state["pipes"].append({
                "x": 400,
                "gap_y": gap_y,
                "passed": False
            })
        
        def draw():
            canvas.delete("all")
            
            # Фон - зірки
            for i in range(20):
                x = (i * 47 + flappy_state["score"] * 2) % 380
                y = (i * 31) % 380
                canvas.create_oval(x, y, x+2, y+2, fill="#4a4a6a", outline="")
            
            # Труби
            for pipe in flappy_state["pipes"]:
                # Верхня труба
                canvas.create_rectangle(
                    pipe["x"], 0, 
                    pipe["x"] + pipe_width, pipe["gap_y"] - pipe_gap//2,
                    fill="#238636", outline="#3fb950", width=2
                )
                # Нижня труба
                canvas.create_rectangle(
                    pipe["x"], pipe["gap_y"] + pipe_gap//2,
                    pipe["x"] + pipe_width, 380,
                    fill="#238636", outline="#3fb950", width=2
                )
                # Кришки труб
                canvas.create_rectangle(
                    pipe["x"] - 5, pipe["gap_y"] - pipe_gap//2 - 20,
                    pipe["x"] + pipe_width + 5, pipe["gap_y"] - pipe_gap//2,
                    fill="#2ea043", outline="#3fb950", width=2
                )
                canvas.create_rectangle(
                    pipe["x"] - 5, pipe["gap_y"] + pipe_gap//2,
                    pipe["x"] + pipe_width + 5, pipe["gap_y"] + pipe_gap//2 + 20,
                    fill="#2ea043", outline="#3fb950", width=2
                )
            
            # Пташка
            y = flappy_state["bird_y"]
            # Тіло
            canvas.create_oval(bird_x - bird_size, y - bird_size, 
                              bird_x + bird_size, y + bird_size, 
                              fill="#ffd33d", outline="#f0c000", width=2)
            # Око
            canvas.create_oval(bird_x + 5, y - 8, bird_x + 15, y + 2, 
                              fill="white", outline="#333")
            canvas.create_oval(bird_x + 9, y - 5, bird_x + 14, y, 
                              fill="#0d1117", outline="")
            # Дзьоб
            canvas.create_polygon(
                bird_x + 15, y,
                bird_x + 30, y + 3,
                bird_x + 15, y + 8,
                fill="#f97316", outline="#c75f00"
            )
            # Крило
            wing_offset = 5 if flappy_state["velocity"] < 0 else -3
            canvas.create_oval(bird_x - 10, y + wing_offset, 
                              bird_x + 5, y + 15 + wing_offset, 
                              fill="#f0c000", outline="#d4a000")
            
            # Земля
            canvas.create_rectangle(0, 360, 380, 380, fill="#2d2d44", outline="#3d3d5c")
            for i in range(0, 380, 40):
                x = (i - flappy_state["score"] * 2) % 400
                canvas.create_line(x, 360, x + 20, 380, fill="#3d3d5c", width=2)
        
        def check_collision():
            y = flappy_state["bird_y"]
            
            # Зіткнення з підлогою/стелею
            if y <= bird_size or y >= 360 - bird_size:
                return True
            
            # Зіткнення з трубами
            for pipe in flappy_state["pipes"]:
                if pipe["x"] < bird_x + bird_size and pipe["x"] + pipe_width > bird_x - bird_size:
                    if y - bird_size < pipe["gap_y"] - pipe_gap//2 or y + bird_size > pipe["gap_y"] + pipe_gap//2:
                        return True
            
            return False
        
        def update():
            if not flappy_state["running"] or flappy_state["game_over"]:
                return
            
            # Гравітація
            flappy_state["velocity"] += gravity
            flappy_state["bird_y"] += flappy_state["velocity"]
            
            # Рух труб
            for pipe in flappy_state["pipes"]:
                pipe["x"] -= pipe_speed
                
                # Підрахунок очок
                if not pipe["passed"] and pipe["x"] + pipe_width < bird_x:
                    pipe["passed"] = True
                    flappy_state["score"] += 1
                    if flappy_state["score"] > flappy_state["best_score"]:
                        flappy_state["best_score"] = flappy_state["score"]
                    score_label.configure(text=f"Рахунок: {flappy_state['score']} | Рекорд: {flappy_state['best_score']}")
            
            # Видалення труб за екраном
            flappy_state["pipes"] = [p for p in flappy_state["pipes"] if p["x"] > -pipe_width]
            
            # Спавн нових труб
            if not flappy_state["pipes"] or flappy_state["pipes"][-1]["x"] < 220:
                spawn_pipe()
            
            # Перевірка зіткнення
            if check_collision():
                flappy_state["game_over"] = True
                flappy_state["running"] = False
                canvas.create_text(190, 170, text="GAME OVER", fill="#da3633", font=("Arial", 24, "bold"))
                canvas.create_text(190, 210, text=f"Рахунок: {flappy_state['score']}", fill="#ffd33d", font=("Arial", 16))
                start_btn.configure(text="🔄 Заново")
                return
            
            draw()
            canvas.after(30, update)
        
        def restart_game():
            """Повний перезапуск гри"""
            flappy_state["bird_y"] = 190
            flappy_state["velocity"] = 0
            flappy_state["pipes"] = []
            flappy_state["score"] = 0
            flappy_state["game_over"] = False
            flappy_state["running"] = True
            score_label.configure(text=f"Рахунок: 0 | Рекорд: {flappy_state['best_score']}")
            spawn_pipe()
            canvas.focus_set()
            draw()
            update()
        
        def jump(event=None):
            if flappy_state["game_over"]:
                # Після game over - перезапуск гри
                restart_game()
                return
            if not flappy_state["running"]:
                restart_game()
                return
            flappy_state["velocity"] = jump_strength
        
        def start_game():
            restart_game()
        
        def toggle_game():
            if flappy_state["game_over"]:
                restart_game()
            elif flappy_state["running"]:
                flappy_state["running"] = False
            else:
                flappy_state["running"] = True
                update()
        
        canvas.bind("<Button-1>", jump)
        canvas.bind("<space>", jump)
        canvas.bind("<Up>", jump)
        
        # Інструкція
        ctk.CTkLabel(game_frame, text="Клік або Пробіл - стрибок", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack()
        
        btn_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
        btn_frame.pack(pady=5)
        
        start_btn = ctk.CTkButton(btn_frame, text="▶️ Старт", width=100, height=35, fg_color=self.colors["success"], hover_color="#2ea043", command=toggle_game)
        start_btn.pack(side="left", padx=5)
        
        restart_btn = ctk.CTkButton(btn_frame, text="🔄 Заново", width=100, height=35, fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=start_game)
        restart_btn.pack(side="left", padx=5)
        
        draw()
    
    # ============ ІСТОРІЯ ФАЙЛІВ ============
    
    def _load_recent_files(self):
        """Завантаження історії файлів"""
        recent_file = Path("recent_files.json")
        if recent_file.exists():
            try:
                with open(recent_file, "r", encoding="utf-8") as f:
                    self.recent_files = json.load(f)
            except:
                self.recent_files = []
    
    def _save_recent_files(self):
        """Збереження історії файлів"""
        with open("recent_files.json", "w", encoding="utf-8") as f:
            json.dump(self.recent_files[:10], f, ensure_ascii=False)  # Зберігаємо останні 10
    
    def _add_to_recent(self, file_path):
        """Додавання файлу в історію"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:10]  # Максимум 10 файлів
        self._save_recent_files()
    
    def _show_recent_files(self):
        """Показати меню останніх файлів"""
        if not self.recent_files:
            self._update_status("📂 Історія файлів порожня", self.colors["text_muted"])
            return
        
        # Створюємо popup меню
        menu = ctk.CTkToplevel(self)
        menu.title("Останні файли")
        menu.geometry("500x400")
        menu.configure(fg_color=self.colors["bg_dark"])
        menu.transient(self)
        menu.grab_set()
        set_dark_title_bar(menu)
        
        # Заголовок
        ctk.CTkLabel(
            menu, text="📂 Останні файли",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text"]
        ).pack(pady=(20, 15))
        
        # Список файлів
        list_frame = ctk.CTkScrollableFrame(menu, fg_color=self.colors["bg_card"],
                                             corner_radius=10, height=280)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        for file_path in self.recent_files:
            file_name = Path(file_path).name
            file_dir = str(Path(file_path).parent)[:40] + "..."
            
            item_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=3)
            
            def open_file(fp=file_path, m=menu):
                m.destroy()
                self._open_recent_file(fp)
            
            btn = ctk.CTkButton(
                item_frame, text=f"📄 {file_name}",
                anchor="w",
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                hover_color=self.colors["bg_input"],
                text_color=self.colors["text"],
                command=open_file
            )
            btn.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                item_frame, text=file_dir,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_muted"]
            ).pack(side="right", padx=10)
        
        # Кнопка закриття
        ctk.CTkButton(menu, text="Закрити", width=120, height=35,
                      fg_color=self.colors["bg_input"], hover_color=self.colors["border"],
                      command=menu.destroy).pack(pady=(0, 20))
    
    def _open_recent_file(self, file_path):
        """Відкриття файлу з історії"""
        if Path(file_path).exists():
            self.file_path = file_path
            self.file_label.configure(text=f"📄 {Path(file_path).name}")
            self._load_file()
        else:
            messagebox.showwarning("Файл не знайдено", f"Файл більше не існує:\n{file_path}")
            self.recent_files.remove(file_path)
            self._save_recent_files()
    
    # ============ СТАТИСТИКА ТЕКСТУ ============
    
    def _update_text_stats(self):
        """Оновлення статистики тексту"""
        text = self.original_text.get("1.0", "end-1c")
        
        # Підрахунок
        chars = len(text)
        words = len(text.split())
        lines = len(text.split("\n"))
        
        self.stats_label.configure(text=f"📊 {words} слів | {chars} символів | {lines} рядків")
    
    # ============ АВТОЗБЕРЕЖЕННЯ ============
    
    def _start_autosave(self):
        """Запуск автозбереження"""
        if self.autosave_enabled and self.is_translating and self.translated_lines:
            # Зберігаємо в тимчасовий файл
            try:
                autosave_path = Path("autosave_translation.txt")
                with open(autosave_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.translated_lines))
            except:
                pass
        
        # Запланувати наступне автозбереження
        if self.is_translating:
            self.after(self.autosave_interval * 1000, self._start_autosave)


def main():
    app = TranslatorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

