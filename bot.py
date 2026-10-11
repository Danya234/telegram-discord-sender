import os
import html
import time
import smtplib
import traceback
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.header import Header
from threading import Thread
from flask import Flask
import discord

# ================= НАСТРОЙКИ =================
# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "ВАШ_ТОКЕН_ТЕЛЕГРАМ")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ВАШ_CHAT_ID")

# Яндекс Почта
YANDEX_USER = os.environ.get("YANDEX_USER", "vash_login@yandex.ru")  # Ваш адрес @yandex.ru
YANDEX_PASS = os.environ.get("YANDEX_PASS", "пароль_приложения")     # 16-значный пароль приложения
YANDEX_TO = os.environ.get("YANDEX_TO", YANDEX_USER)                 # Куда слать (по умолчанию на этот же ящик)

# Discord
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "ВАШ_ТОКЕН_ДИСКОРДА")
TARGET_GUILD_ID = 1541087180297076756  # Ваш целевой сервер
TARGET_CHANNELS = []                    # Пустой список = все каналы сервера
# =============================================

# --- ВЕБ-СЕРВЕР АНТИ-СНА НА RENDER ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "✅ Discord-to-Telegram & Yandex Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

# --- ЛОГИКА ДИСКОРД СЛУШАТЕЛЯ ---
class DiscordNotifier(discord.Client):
    async def on_ready(self):
        print(f"✅ Успешное подключение к Discord: {self.user.name}")
        print(f"🎯 Отслеживается сервер ID: {TARGET_GUILD_ID}")

    async def on_message(self, message):
        # 1. Игнорируем собственные сообщения
        if message.author == self.user:
            return

        # 2. Фильтр сервера
        if not message.guild or message.guild.id != TARGET_GUILD_ID:
            return

        # 3. Фильтр каналов
        if TARGET_CHANNELS and message.channel.id not in TARGET_CHANNELS:
            return

        server_name = message.guild.name
        channel_name = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "Канал"
        author_name = message.author.display_name
        author_tag = message.author.name

        raw_content = message.clean_content or "[Вложение, стикер или эмбед]"
        safe_content = html.escape(raw_content)

        # 1. Форматирование для Telegram
        tg_text = (
            f"🔔 <b>{html.escape(server_name)}</b> | <code>{html.escape(channel_name)}</code>\n"
            f"👤 <b>{html.escape(author_name)}</b> (@{author_tag}):\n\n"
            f"{safe_content}"
        )

        # 2. Форматирование для Яндекс Почты
        email_subject = f"Discord: {author_name} в {channel_name}"
        email_body = f"Сервер: {server_name}\nКанал: {channel_name}\nАвтор: {author_name} (@{author_tag})\n\n{raw_content}"

        # Отправка в Telegram
        self.send_telegram(tg_text)

        # Отправка на Яндекс Почту (в фоновом потоке, чтобы бот не зависал)
        Thread(target=self.send_yandex_mail, args=(email_subject, email_body)).start()

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

    def send_yandex_mail(self, subject, body):
        if not YANDEX_USER or not YANDEX_PASS or "пароль" in YANDEX_PASS:
            return
        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = YANDEX_USER
            msg['To'] = YANDEX_TO

            # Подключение к SMTP серверу Яндекса
            with smtplib.SMTP_SSL('smtp.yandex.ru', 465, timeout=10) as server:
                server.login(YANDEX_USER, YANDEX_PASS)
                server.sendmail(YANDEX_USER, [YANDEX_TO], msg.as_string())
        except Exception as e:
            print(f"Ошибка отправки на Яндекс Почту: {e}")

# --- ТОЧКА ЗАПУСКА ---
if __name__ == "__main__":
    keep_alive()

    if not DISCORD_TOKEN or "ВАШ_ТОКЕН" in DISCORD_TOKEN:
        print("❌ ОШИБКА: DISCORD_TOKEN не задан!")
        while True:
            time.sleep(3600)

    client = DiscordNotifier()
    try:
        print("⏳ Запуск бота...")
        client.run(DISCORD_TOKEN)
    except Exception as e:
        print("❌ ОШИБКА ПРИ ВХОДЕ В DISCORD:")
        print(traceback.format_exc())
        while True:
            time.sleep(3600)
