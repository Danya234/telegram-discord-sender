import discord
import urllib.request
import urllib.parse
import html

# ================= НАСТРОЙКИ =================
# Токен бота Telegram (получить у @BotFather)
TELEGRAM_BOT_TOKEN = "ВАШ_ТОКЕН_ТЕЛЕГРАМ_БОТА"

# Ваш личный цифровой ID в Telegram (узнать у бота @userinfobot)
TELEGRAM_CHAT_ID = "ВАШ_CHAT_ID"

# Ваш личный токен Discord (User Token)
DISCORD_TOKEN = "ВАШ_ТОКЕН_ДИСКОРДА"

# Если хотите слушать ТОЛЬКО конкретные каналы — укажите их ID через запятую: [123456789, 987654321]
# Если оставить список пустым [], бот будет присылать сообщения ВООБЩЕ СО ВСЕХ каналов и серверов:
TARGET_CHANNELS = [] 
# =============================================

class DiscordToTelegram(discord.Client):
    async def on_ready(self):
        print(f"✅ Успешно подключено к Discord под аккаунтом: {self.user.name}")

    async def on_message(self, message):
        # Игнорируем сообщения, которые написали вы сами
        if message.author == self.user:
            return

        # Фильтр каналов (если список не пустой)
        if TARGET_CHANNELS and message.channel.id not in TARGET_CHANNELS:
            return

        # Определяем откуда сообщение
        server_name = message.guild.name if message.guild else "Личные сообщения"
        channel_name = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "ЛС"
        author_name = message.author.display_name
        author_tag = message.author.name
        
        # Экранируем спецсимволы для HTML
        content = html.escape(message.clean_content) if message.clean_content else "<i>[Вложение, стикер или эмбед]</i>"
        safe_server = html.escape(server_name)
        safe_channel = html.escape(channel_name)
        safe_author = html.escape(author_name)

        # Форматируем текст для Telegram
        text = (
            f"🔔 <b>{safe_server}</b> | <code>{safe_channel}</code>\n"
            f"👤 <b>{safe_author}</b> (@{author_tag}):\n\n"
            f"{content}"
        )

        # Отправляем в Telegram
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
            print(f"Ошибка при отправке в Telegram: {e}")

if __name__ == "__main__":
    client = DiscordToTelegram()
    # Запуск от имени пользователя (selfbot)
    client.run(DISCORD_TOKEN)
