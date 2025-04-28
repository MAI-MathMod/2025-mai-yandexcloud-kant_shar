import telebot
from telebot import types
from dotenv import load_dotenv
import os
import logging
from functions import save_user, update_user_role, get_all_admin_ids, stay_in_quire, create_dialog


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
Задавай свои вопросы, я с радостью на них отвечу.
Если ты админ, пришли admin.'''

    save_user(message.chat.id, user_nick=message.chat.username,role='user')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_admin = types.KeyboardButton("Связаться с админом")
    markup.add(button_admin)
    bot.send_message(message.chat.id, text_first, reply_markup=markup)


@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text == 'Hello!':
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Hello!', reply_markup=markup)

    if message.text == 'admin':
        text = 'Введи код.'
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, text, reply_markup=markup)

    if message.text == '12345':
        if update_user_role(str(message.chat.id), 'admin'):
            text = 'Вы успешно зарегистрированы как админ'
            markup = types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id, text, reply_markup=markup)
        else:
            text = 'Пароль верен, попробуйте позже или свяжитесь с админом'
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button_admin = types.KeyboardButton("Связаться с админом")
            markup.add(button_admin)
            bot.send_message(message.chat.id, text, reply_markup=markup)

    if message.text == "Связаться с админом":
        admins = get_all_admin_ids()
        if len(admins) == 0:
            markup = types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id, 'Технические шоколадки, попробуйте позже', reply_markup=markup)
        else:
            stay_in_quire(str(message.chat.id))
            for id in admins:
                text = 'С вами хотят связаться.'
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                button_agree = types.KeyboardButton('Подтвердить')
                markup.add(button_agree)
                bot.send_message(id, text, reply_markup=markup)

    if message.text == 'Подтвердить':
        create_dialog(message.chat.id)
        admins = get_all_admin_ids()
        for id in admins:
            if id != str(message.chat.id):
                text = 'На вопрос ответил другой админ'
                markup = types.ReplyKeyboardRemove()
                bot.send_message(id, text, reply_markup=markup)
        text = '''Спасибо за вашу инициативность.
Перенаправляю на чат с пользователем.'''
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, text, reply_markup=markup)



def send_message_to_user(from_user, to_user, text):
    """
    Функция для отправки сообщения от одного пользователя другому через бота.

    Аргументы:
    from_user: имя пользователя, который отправляет сообщение.
    to_user: имя пользователя, которому отправляется сообщение.
    text: текст сообщения.
    """
    # Проверяем, есть ли указанные пользователи в базе данных
    if from_user in user_data and to_user in user_data:
        from_user_chat_id = user_data[from_user]['chat_id']
        to_user_chat_id = user_data[to_user]['chat_id']

        # Отправляем сообщение пользователю
        bot.send_message(to_user_chat_id, f"Сообщение от {from_user}: {text}")

        # Можно отправить уведомление отправителю (по желанию)
        bot.send_message(from_user_chat_id, f"Вы отправили сообщение пользователю {to_user}: {text}")
    else:
        print("Один из пользователей не найден в базе данных.")


bot.infinity_polling()