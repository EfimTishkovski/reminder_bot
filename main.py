import telebot
from telebot import types
import sqlite3

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

# Инициализация
# Подключение к БД
try:
    connection = sqlite3.connect('users_data.db')
    cursor = connection.cursor()
    query = ''
    cursor.execute(query)
    answer = cursor.fetchall() # получение данных из запроса qwery
    cursor.close()
    connection.close()
    print('Отработало')
except sqlite3.Error as erorr:
    print(f'Ошибка:{erorr}')

# Написать блок инициализации
# Подключение к БД, создание курсора
# Проверка базы на старые, просроченные события и их удаление.

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
