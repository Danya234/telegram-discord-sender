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

# Mail.ru
MAIL_USER = os.environ.get("MAIL_USER", "vash_box@mail.ru")        # Ваш адрес @mail.ru
MAIL_PASS = os.environ.get("MAIL_PASS", "пароль_приложения_сюда") # Пароль для внешних приложений
MAIL_TO = os.environ.get("MAIL_TO", MAIL_USER)                    # Куда слать (обычно тот же ящик)

# Discord
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "ВАШ_ТОКЕН_ДИСКОРДА")
TARGET_GUILD_ID = 1541087180297076756  # Ваш сервер
TARGET_CHANNELS = []
# =============================================

# --- ВЕБ-СЕРВЕР АНТИ-СНА НА RENDER ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "✅ Discord-to-Telegram & Mail.ru Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

# --- ЛОГИКА ДИСКОРД БОТА ---
class DiscordNotifier(discord.Client):
    async def on_ready(self):
        print(f"✅ Успешное подключение к Discord: {self.user.name}")
        print(f"🎯 Отслеживается сервер ID: {TARGET_GUILD_ID}")

    async def on_message(self, message):
        # 1. Игнорируем свои сообщения
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

        # Текст для Telegram
        tg_text = (
            f"🔔 <b>{html.escape(server_name)}</b> | <code>{html.escape(channel_name)}</code>\n"
            f"👤 <b>{html.escape(author_name)}</b> (@{author_tag}):\n\n"
            f"{safe_content}"
        )

        # Тема и текст для Почты
        email_subject = f"Discord: {author_name} в {channel_name}"
        email_body = f"Сервер: {server_name}\nКанал: {channel_name}\nАвтор: {author_name} (@{author_tag})\n\n{raw_content}"

        # Отправляем в Telegram
        self.send_telegram(tg_text)

        # Отправляем на Mail.ru (в отдельном потоке, чтобы не тормозить бот)
        Thread(target=self.send_mail, args=(email_subject, email_body)).start()

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

    def send_mail(self, subject, body):
        if not MAIL_USER or not MAIL_PASS:
            return
        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = MAIL_USER
            msg['To'] = MAIL_TO

            with smtplib.SMTP_SSL('smtp.mail.ru', 465, timeout=10) as server:
                server.login(MAIL_USER, MAIL_PASS)
                server.sendmail(MAIL_USER, [MAIL_TO], msg.as_string())
        except Exception as e:
            print(f"Ошибка отправки на Mail.ru: {e}")

# --- ЗАПУСК ---
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
