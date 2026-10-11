import os
import html
import urllib.request
import urllib.parse
from threading import Thread
from flask import Flask
import discord

# ================= НАСТРОЙКИ =================
# Токены берутся из переменных Render (или впишите вручную в кавычки)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ТЕЛЕГРАМ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ВАШ_CHAT_ID")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "ВАШ_ТОКЕН_ДИСКОРДА")

# Если список пустой [], бот слушает ВСЕ каналы и серверы.
# Если нужны конкретные каналы — укажите их ID числами: [123456789, 987654321]
TARGET_CHANNELS = []
# =============================================

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (ЧТОБЫ НЕ ЗАСЫПАЛ) ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "✅ Discord-to-Telegram Bot is running 24/7!"

def run_web_server():
    # Render передает свой порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

# --- ЛОГИКА ДИСКОРД БОТА ---
class DiscordToTelegram(discord.Client):
    async def on_ready(self):
        print(f"✅ Успешное подключение к Discord под аккаунтом: {self.user.name}")

    async def on_message(self, message):
        # Игнорируем собственные сообщения
        if message.author == self.user:
            return

        # Фильтр каналов (если задан)
        if TARGET_CHANNELS and message.channel.id not in TARGET_CHANNELS:
            return

        # Получаем данные сообщения
        server_name = message.guild.name if message.guild else "Личные сообщения"
        channel_name = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "ЛС"
        author_name = message.author.display_name
        author_tag = message.author.name

        # Экранируем спецсимволы для безопасного HTML в Telegram
        content = html.escape(message.clean_content) if message.clean_content else "<i>[Вложение, стикер или эмбед]</i>"
        safe_server = html.escape(server_name)
        safe_channel = html.escape(channel_name)
        safe_author = html.escape(author_name)

        text = (
            f"🔔 <b>{safe_server}</b> | <code>{safe_channel}</code>\n"
            f"👤 <b>{safe_author}</b> (@{author_tag}):\n\n"
            f"{content}"
        )

        self.send_telegram(text)

    def send_telegram(self, text):
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        d
