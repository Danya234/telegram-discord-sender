import os
import html
import time
import traceback
import urllib.request
import urllib.parse
from threading import Thread
from flask import Flask
import discord

# ================= НАСТРОЙКИ =================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ТЕЛЕГРАМ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ВАШ_CHAT_ID")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "ВАШ_ТОКЕН_ДИСКОРДА")

# ID вашего целевого сервера (сообщения будут идти ТОЛЬКО с него)
TARGET_GUILD_ID = 1541087180297076756

# Если нужны только конкретные каналы на этом сервере — укажите их ID: [123, 456].
# Если оставить пустым [], бот будет присылать сообщения со ВСЕХ каналов этого сервера:
TARGET_CHANNELS = []
# =============================================

# --- ВЕБ-СЕРВЕР ДЛЯ АНТИ-СНА НА RENDER ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "✅ Discord-to-Telegram Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

# --- ЛОГИКА СЛУШАТЕЛЯ DISCORD ---
class DiscordToTelegram(discord.Client):
    async def on_ready(self):
        print(f"✅ Успешное подключение к Discord под аккаунтом: {self.user.name}")
        print(f"🎯 Фильтр включён: отслеживается только сервер с ID {TARGET_GUILD_ID}")

    async def on_message(self, message):
        # 1. Игнорируем сообщения от самого себя
        if message.author == self.user:
            return

        # 2. ФИЛЬТР: игнорируем ЛС и все остальные серверы
        if not message.guild or message.guild.id != TARGET_GUILD_ID:
            return

        # 3. Фильтр каналов внутри сервера (если список не пустой)
        if TARGET_CHANNELS and message.channel.id not in TARGET_CHANNELS:
            return

        server_name = message.guild.name
        channel_name = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "Канал"
        author_name = message.author.display_name
        author_tag = message.author.name

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
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true"
        }).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"Ошибка отправки в Telegram: {e}")

# --- ТОЧКА ЗАПУСКА С ПЕРЕХВАТОМ ОШИБОК ---
if __name__ == "__main__":
    # Запуск веб-сервера анти-сна
    keep_alive()

    # Проверка наличия токена
    if not DISCORD_TOKEN or "ВАШ_ТОКЕН" in DISCORD_TOKEN:
        print("❌ ОШИБКА: Токен Discord не указан в переменных окружения!")
        while True:
            time.sleep(3600)

    client = DiscordToTelegram()
    try:
        print("⏳ Попытка входа в Discord...")
        client.run(DISCORD_TOKEN)
    except Exception as e:
        print("❌ ОШИБКА ПРИ ВХОДЕ В DISCORD:")
        print(traceback.format_exc())
        print("ℹ️ Сервис не выключается, чтобы логи оставались доступны.")
        while True:
            time.sleep(3600)
