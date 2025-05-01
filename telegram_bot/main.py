import telebot
from telebot import types
from config import Config
import logging
from functions import *
from assistant.assistant import *
from database_logic.database_fucns import *
from telegram_bot.functions import get_or_create_assistant, clear_assistants

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
config = Config(_env_file='../.env')
if not config.bot_token:
    logger.error("Не указан TELEGRAM_BOT_TOKEN в .env файле!")
    exit(1)

bot = telebot.TeleBot(config.bot_token)
calling_admin = dict()
assistants = dict()


bot.set_my_commands([
    types.BotCommand("start", "Начать работу с ботом"),
    types.BotCommand("help", "Помощь и информация о боте")
])


@bot.message_handler(commands=['start'])
def start_message(message):
    text_first = '''Привет! Я бот приемной комиссии МАИ. Задавай свои вопросы, я с радостью на них отвечу.
Нажмите на кнопку снизу, чтобы установить язык (Press the button below to chose language). Можете не нажимать, если хотите оставить русский язык.'''
    save_user(message.chat.id, user_nick=message.chat.username,role='user')
    get_or_create_assistant(assistants, message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_change_language = types.KeyboardButton('Change language')
    markup.add(btn_change_language)
    bot.send_message(message.chat.id, text_first, reply_markup=markup)
    sticker_id = 'CAACAgIAAxkBAAICNWgTIyky78MuNmqEx1QAAaqonH7nFwACdm8AAutXmUgw_YYIBsfs6TYE'
    bot.send_sticker(message.chat.id, sticker_id)


@bot.message_handler(commands=['help'])
def help_message(message):
    help_text = '''Доступные команды:
/start - Начать диалог с ботом
/help - Получить справку'''

    bot.send_message(message.chat.id, help_text)


@bot.message_handler(func=lambda message: message.text == 'Change language')
def change_language(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Please enter new language.", reply_markup=markup)
    bot.register_next_step_handler(message, process_language)


def process_language(message):
    new_language = message.text
    clear_assistants(assistants, message.chat.id)
    get_or_create_assistant(assistants, message.chat.id, language=new_language)
    bot.send_message(message.chat.id, f"You chose language: {new_language}. "
                                      f"Now type message and assistant will use it.")


@bot.message_handler(commands=['admin'])
def admin_registration(message):
    if len(message.text.split(' ')) != 2:
        text = 'Команда использована неверно, отправьте ее заново (правильный вид - /admin "пароль").'
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, text, reply_markup=markup)
    if message.text.split(' ')[1] == config.password:
        update_user(message.chat.id, 'role', 'admin')
        text = 'Вы успешно зарегистрированы как админ.'
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'queue_position')
def handle_queue_position(call):
    queue_button = types.InlineKeyboardMarkup()
    queue_button.add(types.InlineKeyboardButton(text='Узнать место в очереди', callback_data='queue_position'))

    chat_id = call.message.chat.id
    message_id = call.message.message_id

    place = stay_in_quire(chat_id)
    if place is True:  # Если очередь пуста или пользователь первый
        text = 'Вы следующий в очереди!'
    elif place:  # Если есть конкретная позиция
        text = f'Вы в очереди на {place} месте.'
    else:  # Если пользователя нет в очереди
        text = 'Вы не в очереди.'

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=queue_button
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def handle_confirmation(call):
    user_id = call.data.split('_')[1]

    admins = get_all_admin_ids()
    for admin_id in admins:
        if admin_id in calling_admin:
            try:
                bot.delete_message(admin_id, calling_admin[admin_id])
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")
            finally:
                calling_admin.pop(admin_id, None)

    if create_dialog(call.message.chat.id):
        text = '''Спасибо за вашу инициативность.
        Перенаправляю на чат с пользователем.'''
        bot.send_message(call.message.chat.id, text)

        bot.send_message(user_id, 'Администратор принял ваш запрос. Можете общаться.')
    else:
        text = 'Извините, но вы уже ведете диалог с другим пользователем. Завершите текущий диалог, чтобы начать новый.'
        bot.send_message(call.message.chat.id, text)


@bot.message_handler(content_types='text')
def message_reply(message):
    visavi = get_visavi(message.chat.id)
    user_id = message.chat.id
    priem_agent = get_or_create_assistant(assistants, user_id)

    if str(user_id) in get_all_admin_ids():
        if visavi:
            if message.text == 'Закончить беседу':
                clear_assistants(assistants, user_id)
                stop_dialog(user_id)
                markup = types.ReplyKeyboardRemove()
                bot.send_message(user_id, 'Спасибо за беседу, контакт разорван.', reply_markup=markup)
                bot.send_message(visavi, 'Спасибо за беседу, контакт разорван.', reply_markup=markup)
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                button_stop = types.KeyboardButton("Закончить беседу")
                markup.add(button_stop)
                bot.send_message(visavi, message.text, reply_markup=markup)
        else:
            bot.send_message(user_id, "Вы не в диалоге с пользователем")
    elif priem_agent.get_handover():
        if visavi:
            if message.text == 'Закончить беседу':
                clear_assistants(assistants, user_id)
                stop_dialog(user_id)
                bot.send_message(user_id, 'Спасибо за беседу, контакт разорван.')
                bot.send_message(visavi, 'Спасибо за беседу, контакт разорван.')
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                button_stop = types.KeyboardButton("Закончить беседу")
                markup.add(button_stop)
                bot.send_message(visavi, message.text, reply_markup=markup)
        else:
            admins = get_all_admin_ids()
            if len(admins) == 0:
                markup = types.ReplyKeyboardRemove()
                bot.send_message(user_id, 'Технические шоколадки, попробуйте позже',
                                 reply_markup=markup)

    elif str(user_id) not in get_all_admin_ids():
        text = priem_agent(message.text)
        ms = bot.send_message(user_id, text)

        if priem_agent.get_handover():
            admins = get_all_admin_ids()
            for id in admins:
                history = '\n'
                for msg in list(priem_agent.get_thread())[::-1]:
                    history = f'{history}{msg.author.role}:** {msg.text}\n'
                text_for_admin = (f'С вами хотят связаться.'
                        f'Вот история переписки ассистента и пользователя:\n{history}')
                markup = types.InlineKeyboardMarkup()
                button_agree = types.InlineKeyboardButton(
                    '✅Подтвердить',
                    callback_data=f'confirm_{message.chat.id}'
                )
                markup.add(button_agree)
                mes_id = bot.send_message(id, text_for_admin, reply_markup=markup)
                calling_admin[id] = mes_id.message_id

            place = stay_in_quire(user_id)
            if place and place is not True:
                text = f'Вы уже в очереди на {place} месте.'
                bot.send_message(user_id, text)
            else:
                markup = types.InlineKeyboardMarkup()
                button_text = 'Узнать положение в очереди'
                button_agree = types.InlineKeyboardButton(button_text, callback_data='queue_position')
                markup.add(button_agree)
                bot.edit_message_text(chat_id=user_id, message_id=ms.message_id, text=text, reply_markup=markup)
                sticker_id = 'CAACAgIAAxkBAAICOmgTI7jY8QjJENvmTaTgPyW3xtYzAAJTcwACEIOYSIIQbF12KpNtNgQ'
                bot.send_sticker(message.chat.id, sticker_id)


bot.infinity_polling()