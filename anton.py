import sys
import os
import json
import asyncio
from pathlib import Path
from threading import Thread

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QListWidget,
    QFrame, QGraphicsDropShadowEffect, QScrollArea, QStackedWidget,
    QMessageBox, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QLinearGradient, QPixmap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
API_KEY_FILE = os.path.join(BASE_DIR, "Илона.txt")
AVATAR_FILE = os.path.join(BASE_DIR, "avatar.jpg")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"profile": {}, "knowledge": {}, "skills": [], "telegram": {}}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return ""


class GlassCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 130);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 80);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)


class TabButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #6a6a6a;
                border: none;
                border-radius: 12px;
                font-size: 13px;
                font-family: 'Segoe UI Light', sans-serif;
                padding: 0 16px;
            }
            QPushButton:hover { color: #3a3a3a; }
            QPushButton:checked {
                background: rgba(50, 50, 80, 100);
                color: #1a1a1a;
            }
        """)


class AIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_key, messages):
        super().__init__()
        self.api_key = api_key
        self.messages = messages

    def run(self):
        try:
            client = Groq(api_key=self.api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.messages,
                temperature=0.7,
                max_tokens=1500
            )
            self.finished.emit(response.choices[0].message.content.strip())
        except Exception as e:
            self.error.emit(str(e))


class TelegramBot:
    def __init__(self, config):
        self.config = config
        self.app = None
        self.thread = None
        self.running = False

    def build_system_prompt(self):
        p = self.config.get("profile", {})
        k = self.config.get("knowledge", {})
        skills = self.config.get("skills", [])

        products = "\n".join(k.get("products", []))
        prices = "\n".join(k.get("prices", []))
        faq = "\n".join(k.get("faq", []))

        return f"""Ты — {p.get('name', 'Ассистент')}, {p.get('specialization', 'специалист')}.
Компания: {p.get('company', 'Не указана')}
Описание: {p.get('description', '')}
Тон общения: {p.get('tone', 'Профессиональный')}

Твои навыки:
{chr(10).join('- ' + s for s in skills) if skills else '- Консультация'}

Товары и услуги:
{products if products else 'Информация не добавлена'}

Цены:
{prices if prices else 'Информация не добавлена'}

Частые вопросы:
{faq if faq else 'Информация не добавлена'}

Правила:
- Отвечай на русском
- Будь вежливой и helpful
- Если не знаешь ответ — скажи что уточнишь у специалиста
- Не выдумывай информацию, которой нет в базе
- Отвечай кратко и по делу"""

    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        p = self.config.get("profile", {})
        greeting = p.get("greeting", "Здравствуйте! Чем могу помочь?")
        await update.message.reply_text(greeting)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_text = update.message.text
        api_key = get_api_key()

        if not api_key:
            await update.message.reply_text("Сервис временно недоступен. Попробуйте позже.")
            return

        system = self.build_system_prompt()
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text}
        ]

        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            reply = response.choices[0].message.content.strip()
            await update.message.reply_text(reply)
        except Exception as e:
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

    def run_bot(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        token = self.config.get("telegram", {}).get("token", "")
        if not token:
            return

        self.app = Application.builder().token(token).build()
        self.app.add_handler(CommandHandler("start", self.start_cmd))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        self.running = True
        self.app.run_polling()

    def start(self, config):
        self.config = config
        if self.running:
            return
        self.thread = Thread(target=self.run_bot, daemon=True)
        self.thread.start()

    def stop(self):
        if self.app:
            self.app.stop()
            self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Илона - Обучающийся ассистент")
        self.setFixedSize(480, 780)
        self.config = load_config()
        self.current_page = 0
        self.bot = TelegramBot(self.config)
        self.bot_running = False

        self.init_ui()
        self.load_profile()
        self.update_tg_status()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(24, 30, 24, 30)
        main_layout.setSpacing(16)

        header = QLabel("Илона")
        header.setFont(QFont("Segoe UI Light", 32))
        header.setStyleSheet("color: #1a1a1a; background: transparent;")
        main_layout.addWidget(header)

        sub = QLabel("обучающийся ассистент")
        sub.setFont(QFont("Segoe UI Light", 14))
        sub.setStyleSheet("color: #8a8a8a; background: transparent; margin-bottom: 4px;")
        main_layout.addWidget(sub)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(6)
        self.tab_buttons = []
        tabs = ["Профиль", "Знания", "Навыки", "Telegram", "Чат"]
        for i, name in enumerate(tabs):
            btn = TabButton(name)
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            nav_layout.addWidget(btn)
            self.tab_buttons.append(btn)
        main_layout.addLayout(nav_layout)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: transparent; }")
        self.stack.addWidget(self._build_profile_page())
        self.stack.addWidget(self._build_knowledge_page())
        self.stack.addWidget(self._build_skills_page())
        self.stack.addWidget(self._build_telegram_page())
        self.stack.addWidget(self._build_chat_page())
        main_layout.addWidget(self.stack)

        main_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.switch_page(0)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor("#f0f0f5"))
        grad.setColorAt(1, QColor("#e5e5ea"))
        p.fillRect(self.rect(), QBrush(grad))

    def switch_page(self, idx):
        self.current_page = idx
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == idx)

    def _build_profile_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(14)

        card = GlassCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(12)

        avatar_layout = QHBoxLayout()
        avatar_layout.setSpacing(16)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(80, 80)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border-radius: 40px;
                border: 2px solid rgba(0,0,0,0.1);
                background: rgba(0,0,0,0.05);
            }
        """)
        self.avatar_label.setScaledContents(True)
        if os.path.exists(AVATAR_FILE):
            pixmap = QPixmap(AVATAR_FILE)
            self.avatar_label.setPixmap(pixmap)
        else:
            self.avatar_label.setText("Фото")
            self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.avatar_label.setFont(QFont("Segoe UI Light", 10))
            self.avatar_label.setStyleSheet(self.avatar_label.styleSheet() + "color: #8a8a8a;")
        avatar_layout.addWidget(self.avatar_label)

        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        name_col.addWidget(self._label("ИМЯ"))
        self.name_input = self._input("Илона")
        name_col.addWidget(self.name_input)
        avatar_layout.addLayout(name_col)
        avatar_layout.addStretch()

        cl.addLayout(avatar_layout)

        cl.addWidget(self._label("СПЕЦИАЛИЗАЦИЯ"))
        self.spec_input = self._input("Продажа кухонь")
        cl.addWidget(self.spec_input)

        cl.addWidget(self._label("КОМПАНИЯ"))
        self.company_input = self._input("Название компании")
        cl.addWidget(self.company_input)

        cl.addWidget(self._label("ОПИСАНИЕ"))
        self.desc_input = self._input("Помощник по подбору и продаже кухонь")
        cl.addWidget(self.desc_input)

        cl.addWidget(self._label("ПРИВЕТСТВИЕ"))
        self.greet_input = self._input("Здравствуйте! Я Илона, ваш помощник по выбору кухни.")
        cl.addWidget(self.greet_input)

        cl.addWidget(self._label("ТОН ОБЩЕНИЯ"))
        self.tone_input = self._input("Дружелюбный, профессиональный")
        cl.addWidget(self.tone_input)

        save_btn = QPushButton("Сохранить профиль")
        save_btn.setMinimumHeight(48)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(50, 50, 80, 180);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-family: 'Segoe UI Light', sans-serif;
            }
            QPushButton:hover { background: rgba(40, 40, 70, 220); }
        """)
        save_btn.clicked.connect(self.save_profile)
        cl.addWidget(save_btn)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_knowledge_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(14)

        card = GlassCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(12)

        cl.addWidget(self._label("БАЗА ЗНАНИЙ"))
        cl.addWidget(self._label_hint("Добавьте информацию о товарах, услугах, ценах, FAQ"))

        cl.addWidget(self._label("ТОВАРЫ / УСЛУГИ"))
        self.products_input = QPlainTextEdit()
        self.products_input.setPlaceholderText("Кухня Модерн - от 80 000 руб.\nКухня Классик - от 50 000 руб.\nСтолешница из кварца - от 15 000 руб.")
        self.products_input.setMaximumHeight(100)
        self.products_input.setStyleSheet("""
            QPlainTextEdit {
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                padding: 12px;
                color: #1a1a1a;
                font-size: 13px;
                font-family: 'Segoe UI Light', sans-serif;
            }
        """)
        cl.addWidget(self.products_input)

        cl.addWidget(self._label("ЦЕНЫ"))
        self.prices_input = QPlainTextEdit()
        self.prices_input.setPlaceholderText("Замер - бесплатно\nДоставка - 3 000 руб.\nСборка - от 8 000 руб.")
        self.prices_input.setMaximumHeight(100)
        self.prices_input.setStyleSheet(self.products_input.styleSheet())
        cl.addWidget(self.prices_input)

        cl.addWidget(self._label("FAQ"))
        self.faq_input = QPlainTextEdit()
        self.faq_input.setPlaceholderText("В: Сколько занимает изготовление?\nО: 2-4 недели в зависимости от сложности.\n\nВ: Есть ли гарантия?\nО: Да, гарантия 2 года на все кухни.")
        self.faq_input.setMaximumHeight(120)
        self.faq_input.setStyleSheet(self.products_input.styleSheet())
        cl.addWidget(self.faq_input)

        save_btn = QPushButton("Сохранить знания")
        save_btn.setMinimumHeight(48)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(50, 50, 80, 180);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-family: 'Segoe UI Light', sans-serif;
            }
            QPushButton:hover { background: rgba(40, 40, 70, 220); }
        """)
        save_btn.clicked.connect(self.save_knowledge)
        cl.addWidget(save_btn)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_skills_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(14)

        card = GlassCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(12)

        cl.addWidget(self._label("НАВЫКИ И КОМПЕТЕНЦИИ"))
        cl.addWidget(self._label_hint("Что умеет ваш ассистент"))

        self.skills_list = QListWidget()
        self.skills_list.setMaximumHeight(200)
        self.skills_list.setStyleSheet("""
            QListWidget {
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                padding: 8px;
                color: #1a1a1a;
                font-size: 13px;
                font-family: 'Segoe UI Light', sans-serif;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(0,0,0,0.05);
            }
        """)
        cl.addWidget(self.skills_list)

        add_layout = QHBoxLayout()
        self.skill_input = self._input("Новый навык")
        add_layout.addWidget(self.skill_input)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(44, 44)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(50, 50, 80, 180);
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 20px;
            }
            QPushButton:hover { background: rgba(40, 40, 70, 220); }
        """)
        add_btn.clicked.connect(self.add_skill)
        add_layout.addWidget(add_btn)
        cl.addLayout(add_layout)

        del_btn = QPushButton("Удалить выбранный")
        del_btn.setMinimumHeight(40)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: rgba(180, 50, 50, 150);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 13px;
                font-family: 'Segoe UI Light', sans-serif;
            }
            QPushButton:hover { background: rgba(180, 50, 50, 200); }
        """)
        del_btn.clicked.connect(self.del_skill)
        cl.addWidget(del_btn)

        save_btn = QPushButton("Сохранить навыки")
        save_btn.setMinimumHeight(48)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(50, 50, 80, 180);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-family: 'Segoe UI Light', sans-serif;
            }
            QPushButton:hover { background: rgba(40, 40, 70, 220); }
        """)
        save_btn.clicked.connect(self.save_skills)
        cl.addWidget(save_btn)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_telegram_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(14)

        card = GlassCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(12)

        cl.addWidget(self._label("TELEGRAM БОТ"))
        cl.addWidget(self._label_hint("Создайте бота через @BotFather и вставьте токен"))

        cl.addWidget(self._label("ТОКЕН БОТА"))
        self.tg_token_input = self._input("123456:ABC-DEF...")
        cl.addWidget(self.tg_token_input)

        self.tg_status = QLabel("Статус: Не активен")
        self.tg_status.setFont(QFont("Segoe UI Light", 12))
        self.tg_status.setStyleSheet("color: #aa7a2a; background: transparent;")
        cl.addWidget(self.tg_status)

        save_btn = QPushButton("Сохранить токен")
        save_btn.setMinimumHeight(48)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(50, 50, 80, 180);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-family: 'Segoe UI Light', sans-serif;
            }
            QPushButton:hover { background: rgba(40, 40, 70, 220); }
        """)
        save_btn.clicked.connect(self.save_telegram)
        cl.addWidget(save_btn)

        self.start_btn = QPushButton("Запустить бота")
        self.start_btn.setMinimumHeight(48)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: rgba(50, 140, 80, 180);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-family: 'Segoe UI Light', sans-serif;
            }
            QPushButton:hover { background: rgba(50, 140, 80, 220); }
        """)
        self.start_btn.clicked.connect(self.toggle_bot)
        cl.addWidget(self.start_btn)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_chat_page(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(14)

        card = GlassCard()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        cl.addWidget(self._label("ТЕСТОВЫЙ ЧАТ"))

        self.chat_display = QPlainTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMaximumHeight(300)
        self.chat_display.setStyleSheet("""
            QPlainTextEdit {
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                padding: 12px;
                color: #1a1a1a;
                font-size: 13px;
                font-family: 'Segoe UI Light', sans-serif;
            }
        """)
        cl.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Напишите сообщение...")
        self.chat_input.setFont(QFont("Segoe UI Light", 13))
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                padding: 10px 14px;
                color: #1a1a1a;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_chat)
        input_layout.addWidget(self.chat_input)

        send_btn = QPushButton("->")
        send_btn.setFixedSize(44, 44)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(50, 50, 80, 180);
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 16px;
            }
            QPushButton:hover { background: rgba(40, 40, 70, 220); }
        """)
        send_btn.clicked.connect(self.send_chat)
        input_layout.addWidget(send_btn)
        cl.addLayout(input_layout)

        self.chat_status = QLabel("Введите сообщение для тестирования")
        self.chat_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chat_status.setFont(QFont("Segoe UI Light", 11))
        self.chat_status.setStyleSheet("color: #aaaaaa; background: transparent;")
        cl.addWidget(self.chat_status)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setStyleSheet("color: #8a8a8a; background: transparent; letter-spacing: 1px;")
        return lbl

    def _label_hint(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI Light", 11))
        lbl.setStyleSheet("color: #aaaaaa; background: transparent; margin-bottom: 4px;")
        lbl.setWordWrap(True)
        return lbl

    def _input(self, placeholder=""):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFont(QFont("Segoe UI Light", 14))
        inp.setStyleSheet("""
            QLineEdit {
                background: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                padding: 10px 14px;
                color: #1a1a1a;
            }
            QLineEdit:focus { border: 1px solid rgba(50,50,80,0.3); }
        """)
        return inp

    def load_profile(self):
        p = self.config.get("profile", {})
        self.name_input.setText(p.get("name", ""))
        self.spec_input.setText(p.get("specialization", ""))
        self.company_input.setText(p.get("company", ""))
        self.desc_input.setText(p.get("description", ""))
        self.greet_input.setText(p.get("greeting", ""))
        self.tone_input.setText(p.get("tone", ""))

        k = self.config.get("knowledge", {})
        self.products_input.setPlainText("\n".join(k.get("products", [])))
        self.prices_input.setPlainText("\n".join(k.get("prices", [])))
        self.faq_input.setPlainText("\n".join(k.get("faq", [])))

        self.skills_list.clear()
        for s in self.config.get("skills", []):
            self.skills_list.addItem(s)

        tg = self.config.get("telegram", {})
        self.tg_token_input.setText(tg.get("token", ""))

    def save_profile(self):
        self.config["profile"] = {
            "name": self.name_input.text(),
            "specialization": self.spec_input.text(),
            "company": self.company_input.text(),
            "description": self.desc_input.text(),
            "greeting": self.greet_input.text(),
            "tone": self.tone_input.text()
        }
        save_config(self.config)
        QMessageBox.information(self, "OK", "Профиль сохранён")

    def save_knowledge(self):
        self.config["knowledge"] = {
            "products": self.products_input.toPlainText().split("\n"),
            "prices": self.prices_input.toPlainText().split("\n"),
            "faq": self.faq_input.toPlainText().split("\n")
        }
        save_config(self.config)
        QMessageBox.information(self, "OK", "Знания сохранены")

    def add_skill(self):
        text = self.skill_input.text().strip()
        if text:
            self.skills_list.addItem(text)
            self.skill_input.clear()

    def del_skill(self):
        row = self.skills_list.currentRow()
        if row >= 0:
            self.skills_list.takeItem(row)

    def save_skills(self):
        skills = []
        for i in range(self.skills_list.count()):
            skills.append(self.skills_list.item(i).text())
        self.config["skills"] = skills
        save_config(self.config)
        QMessageBox.information(self, "OK", "Навыки сохранены")

    def save_telegram(self):
        self.config["telegram"]["token"] = self.tg_token_input.text()
        save_config(self.config)
        QMessageBox.information(self, "OK", "Токен сохранён")

    def update_tg_status(self):
        if self.bot_running:
            self.tg_status.setText("Статус: Активен")
            self.tg_status.setStyleSheet("color: #3a7a3a; background: transparent;")
            self.start_btn.setText("Остановить бота")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(180, 50, 50, 180);
                    color: white;
                    border: none;
                    border-radius: 14px;
                    font-size: 15px;
                    font-family: 'Segoe UI Light', sans-serif;
                }
                QPushButton:hover { background: rgba(180, 50, 50, 220); }
            """)
        else:
            self.tg_status.setText("Статус: Не активен")
            self.tg_status.setStyleSheet("color: #aa7a2a; background: transparent;")
            self.start_btn.setText("Запустить бота")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(50, 140, 80, 180);
                    color: white;
                    border: none;
                    border-radius: 14px;
                    font-size: 15px;
                    font-family: 'Segoe UI Light', sans-serif;
                }
                QPushButton:hover { background: rgba(50, 140, 80, 220); }
            """)

    def toggle_bot(self):
        if self.bot_running:
            self.bot.stop()
            self.bot_running = False
        else:
            token = self.config.get("telegram", {}).get("token", "")
            if not token:
                QMessageBox.warning(self, "Ошибка", "Сначала вставьте токен бота")
                return
            self.bot.start(self.config)
            self.bot_running = True
        self.update_tg_status()

    def send_chat(self):
        text = self.chat_input.text().strip()
        if not text:
            return

        self.chat_input.clear()
        self.chat_display.appendPlainText(f"Вы: {text}\n")

        api_key = get_api_key()
        if not api_key:
            self.chat_display.appendPlainText("Илона: Нет API ключа\n")
            return

        system = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ]

        self.chat_status.setText("Думаю...")
        self.chat_input.setEnabled(False)

        self.worker = AIWorker(api_key, messages)
        self.worker.finished.connect(self._on_chat_response)
        self.worker.error.connect(self._on_chat_error)
        self.worker.start()

    def _build_system_prompt(self):
        p = self.config.get("profile", {})
        k = self.config.get("knowledge", {})
        skills = self.config.get("skills", [])

        products = "\n".join(k.get("products", []))
        prices = "\n".join(k.get("prices", []))
        faq = "\n".join(k.get("faq", []))

        return f"""Ты — {p.get('name', 'Ассистент')}, {p.get('specialization', 'специалист')}.
Компания: {p.get('company', 'Не указана')}
Описание: {p.get('description', '')}
Тон общения: {p.get('tone', 'Профессиональный')}

Твои навыки:
{chr(10).join('- ' + s for s in skills) if skills else '- Консультация'}

Товары и услуги:
{products if products else 'Информация не добавлена'}

Цены:
{prices if prices else 'Информация не добавлена'}

Частые вопросы:
{faq if faq else 'Информация не добавлена'}

Правила:
- Отвечай на русском
- Будь вежливой и helpful
- Если не знаешь ответ — скажи что уточнишь у специалиста
- Не выдумывай информацию, которой нет в базе"""

    def _on_chat_response(self, text):
        name = self.config.get('profile', {}).get('name', 'Илона')
        self.chat_display.appendPlainText(f"{name}: {text}\n")
        self.chat_status.setText("")
        self.chat_input.setEnabled(True)
        self.chat_input.setFocus()

    def _on_chat_error(self, error):
        self.chat_display.appendPlainText(f"Ошибка: {error}\n")
        self.chat_status.setText("")
        self.chat_input.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
