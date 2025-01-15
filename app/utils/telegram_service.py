import telegram
from app.config import setting
# Define bot
bot = telegram.Bot(token=setting.TELEGRAM_BOT_TOKEN)


async def send_message_telegram(text):
    # Your Telegram bot initialization code here (if not already done)
    await bot.send_message(chat_id=setting.TELEGRAM_CHAT_ID, text=text)
