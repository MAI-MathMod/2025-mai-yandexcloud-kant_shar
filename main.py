import telebot
from telebot import types
from dotenv import load_dotenv
import os
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
if not BOT_TOKEN:
    logger.error("Не указан TELEGRAM_BOT_TOKEN в .env файле!")
    exit(1)

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))



@bot.message_handler(commands=['start'])
def start_message(message):
    text_first = '''Привет! Я бот приемной комиссии МАИ.
Задавай свои вопросы, я с радостью
на них отвечу.'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(message.chat.id, text_first)

@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text == 'Hello!':
        bot.send_message(message.chat.id, 'Hello!')

bot.infinity_polling()