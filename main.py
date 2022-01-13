import telebot
from telebot import types
import sqlite3
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

# Как вариант написать файлик back
# запихнуть туда функцию подключения к базе, действие передавать
# в аргумент функцией

# Инициализация
# Подключение к БД и проверка на старые и просроченные события
    try:
        connection_ini = sqlite3.connect('users_data.db')
        cursor_ini = connection_ini.cursor()
        query_search = ''
        cursor_ini.execute(query_search)
        answer_ini = cursor_ini.fetchall()  # получение данных из запроса query
        cursor_ini.close()
        connection_ini.close()
        print('Отработало')
    except sqlite3.Error as erorr:
        print(f'Ошибка:{erorr}')

# Функция приветствия, старта. И краткая инструкция.
@rem_bot.message_handler(commands=['start'])
def start(messege):
    rem_bot.send_message(messege.chat.id, 'Привет! Это бот - напоминалка\n' +
                         'Для взаимодействия используйте кнопки снизу\n' +
                         'Вызов помощи "/help"')

    # получение информации о пользователе запустившем бот.
    user_info = {'id' : messege.from_user.id,
                 'Имя' : messege.from_user.first_name,
                 'Имя пользователя' : messege.from_user.username}
    # Проверка на наличие пользователя в базе
    # Есть - хорошо, нету - добавить.
    query_user_in_base = f"SELECT [id] FROM 'users' WHERE [id] = {user_info['id']}" # Запрос на поиск id пользователя
    # Функция абработки результата
    def check_user():
        pass
    base_query(check_user(), query_user_in_base)


    print(user_info)
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
