import telebot
from telebot import types
import datetime
from back import *

# Получение токена
tok = open('TOKEN.txt', 'r')
TOKEN = tok.read()
tok.close()

# Создание экземпляра бота и подключение токена
rem_bot = telebot.TeleBot(TOKEN)

# Условие корректной активации бота и вывод сообщения в консоль
if rem_bot:
    print('Запущено.')
else:
    print('Ошибка запуска.')

# Для размышления: можно при запуске бота сразу подключаться к базе
# Вот в этой строчке
# Но при аварийной остановке программы или простой остановке
# Подключение к базе может быть завершено не корректно и данные могут быть потеряны
# Стоит оно того? Или это напрасные опасения?

# Инициализация
# Подключение к БД и проверка на старые и просроченные события

# Функция приветствия, старта. И краткая инструкция.
@rem_bot.message_handler(commands=['start'])
def start(messege):
    rem_bot.send_message(messege.chat.id, 'Привет! Это бот - напоминалка\n' +
                         'Для взаимодействия используйте кнопки снизу\n' +
                         'Вызов помощи "/help"')

    # Получение информации о пользователе запустившем бот.
    date = datetime.datetime.fromtimestamp(messege.date).strftime('%Y-%m-%d %H:%M:%S') # Время в человеческом формате
    user_info = {'id' : messege.from_user.id,
                 'Имя' : messege.from_user.first_name,
                 'Имя пользователя' : messege.from_user.username,
                 'Дата' : date}
    # Проверка на наличие пользователя в базе
    # Есть - хорошо, нету - добавить.
    query_user_in_base = f"SELECT * FROM 'users' WHERE [id] = {user_info['id']}" # Запрос на поиск id пользователя
    if base_query(query_user_in_base, mode='search'):
        rem_bot.send_message(messege.chat.id, f"Привет, {user_info['Имя']}, я помню тебя.")
    else:
        # Добавление пользователя в базу
        rem_bot.send_message(messege.chat.id, f"Привет, {user_info['Имя']}, я вижу тебя впервые, но запомню.")
        query_user_insert = f"INSERT INTO 'users' ([id],[first_name],[username],[date]) " \
                            f"VALUES ('{user_info['id']}','{user_info['Имя']}'," \
                            f"'{user_info['Имя пользователя']}','{user_info['Дата']}');"
        if base_query(query_user_insert):
            print('Добавлен новый пользователь')
    user_info.clear() # Очистка словаря с данными пользователя

    # Создание кнопок интерфейса бота
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_create_event = types.KeyboardButton('Добавить событие')  # Кнопка создания нового события
    btn_my_event = types.KeyboardButton('Показать мои события')  # Кнопка просмотра активных событий пользователя
    markup.add(btn_create_event, btn_my_event)
    rem_bot.reply_to(messege, 'Кнопки появятся ниже', reply_markup=markup)

# Функация принятия сообщения от пользователя(реакция нажатия на кнопки)
@rem_bot.message_handler(func=lambda messege: True)
def comand_to_bot(messege):
    # Проверка типа сообщения
    if messege.chat.type == 'private':
        if messege.text == 'Добавить событие':
            rem_bot.send_message(messege.chat.id, 'Добавить событие')
        elif messege.text == 'Показать мои события':
            rem_bot.send_message(messege.chat.id, 'Показать мои события')


rem_bot.polling(none_stop=True, interval=0)       # Опрос сервера, не написал ли кто-нибудь?
