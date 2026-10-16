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

TARGET_GUILD_ID = 1541087180297076756  # Ваш целевой сервер
TARGET_CHANNELS = []                    # Пустой список = все каналы сервера
# =============================================

# --- КЛИЕНТ DISCORD ---
class DiscordNotifier(discord.Client):
    async def on_ready(self):
        # Принудительно ставим статус «Невидимка» (оффлайн)
        await self.change_presence(status=discord.Status.invisible)
        print(f"✅ Успешное подключение к Discord: {self.user.name}", flush=True)
        print(f"🎯 Отслеживается сервер ID: {TARGET_GUILD_ID}", flush=True)
        print("👻 Режим скрытности активен: для всех вы ОФФЛАЙН!", flush=True)

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

        tg_text = (
            f"🔔 <b>{html.escape(server_name)}</b> | <code>{html.escape(channel_name)}</code>\n"
            f"👤 <b>{html.escape(author_name)}</b> (@{author_tag}):\n\n"
            f"{safe_content}"
        )

        self.send_telegram(tg_text)

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
            print(f"Ошибка отправки в Telegram: {e}", flush=True)

# Инициализируем клиент со статусом invisible с первой же секунды
client = DiscordNotifier(status=discord.Status.invisible)

# --- ВЕБ-СЕРВЕР АНТИ-СНА НА FLASK ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "✅ Discord-to-Telegram Bot is running 24/7!"

# Скрытая проверка через браузер
@web_app.route('/test')
def trigger_test():
    title = "Тестовое уведомление"
    text = "Проверка связи: бот на Render активен, режим оффлайна работает, пуши в Telegram приходят моментально!"
    client.send_telegram(f"🧪 <b>{title}</b>\n\n{text}")
    return "🚀 Успешно! Тестовое уведомление отправлено в Telegram."

# --- АВТОМАТИЧЕСКИЙ САМО-ПИНГ ---
def self_ping_loop():
    time.sleep(40)
    app_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("SELF_PING_URL")
    
    if not app_url:
        print("⚠️ RENDER_EXTERNAL_URL не найден.", flush=True)
        return

    print(f"🔄 Защита от сна активна для: {app_url}", flush=True)
    while True:
        try:
            req = urllib.request.Request(app_url, headers={'User-Agent': 'KeepAliveBot/1.0'})
            with urllib.request.urlopen(req, timeout=15):
                pass
        except Exception:
            pass
        time.sleep(480)  # Пинг каждые 8 минут

def keep_alive():
    t1 = Thread(target=lambda: web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))))
    t1.daemon = True
    t1.start()

    t2 = Thread(target=self_ping_loop)
    t2.daemon = True
    t2.start()

# --- ТОЧКА ЗАПУСКА С ЗАЩИТОЙ ---
if __name__ == "__main__":
    keep_alive()

    if not DISCORD_TOKEN or "ВАШ_ТОКЕН" in DISCORD_TOKEN:
        print("❌ ОШИБКА: DISCORD_TOKEN не задан!", flush=True)
        while True:
            time.sleep(3600)

    try:
        print("⏳ Запуск Discord слушателя...", flush=True)
        client.run(DISCORD_TOKEN)
    except Exception as e:
        print("❌ ОШИБКА ПРИ ВХОДЕ В DISCORD:", flush=True)
        print(traceback.format_exc(), flush=True)
        while True:
            time.sleep(3600)
