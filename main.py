import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext             # импорт библиотеки с машиной состояний
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import types
from back import *

# Получение токена
tok = open('TOKEN.txt', 'r')
TOKEN = tok.read()
tok.close()

# Инициализация бота
rem_bot = Bot(token=TOKEN)            # Создание экземпляра бота
loop = asyncio.get_event_loop()       # Создание цикла
disp = Dispatcher(rem_bot, loop=loop, storage=MemoryStorage()) # Добавление цикла в диспетчер,
                                                               # Он запустит полинг и цикл с нашей функцией параллельно.
# Информационное сообщение в консоль
if rem_bot:
    print('Запущено.')
else:
    print('Ошибка запуска.')

# Функция получения события от пользователя
# Создание диалога для ввода события пользователем
# Создаём состояния FSM
class FSM_event_user(StatesGroup):
    name = State()
    date = State()
    time = State()

# Начало диалога
@disp.message_handler(lambda message: message.text == 'Добавить событие', state=None)
async def event_start(message: types.Message):
    await FSM_event_user.name.set()
    await rem_bot.send_message(message.chat.id, 'Введите название')

# Ловим название события
@disp.message_handler(state=FSM_event_user.name)
async def event_start(message: types.Message, state: FSMContext):
    async with state.proxy() as data:               # Узнать что это (вроде запись данных)
        data['Название'] = message.text             # получение данных от пользователя в словарь
    await FSM_event_user.next()                     # Переход к следующему состоянию машины
    await FSM_event_user.date.set()                 # Установка к следующего состоянию машины
    await rem_bot.send_message(message.chat.id, 'Введите дату')  # Сообщению пользователю что делать дальше

# Ловим дату события
@disp.message_handler(state=FSM_event_user.date)
async def event_start(message: types.Message, state: FSMContext):
    async with state.proxy() as data:          # Узнать что это (вроде запись данных)
        data['Дата'] = message.text            # получение данных от пользователя в словарь
    await FSM_event_user.next()                # Переход к следующему состоянию машины
    await FSM_event_user.time.set()            # Установка к следующего состоянию машины
    await rem_bot.send_message(message.chat.id, 'Введите время')  # Сообщению пользователю что делать дальше

# Завершение диалога
@disp.message_handler(state=FSM_event_user.time)
async def print_event(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['Время'] = message.text
        # Словарь с данными пользователя
        user_info = {'id': message.from_user.id,
                     'Имя': message.from_user.first_name,
                     'Имя пользователя': message.from_user.username}
        #print(data.as_dict())  # Данные в памяти в виде словаря
        data_event = data.as_dict()   # Данные в памяти в виде словаря
    await rem_bot.send_message(message.chat.id, 'Событие: \n' +
                               f"Пользователь: {user_info['Имя']} \n" +
                               f"Название: {data_event['Название']} \n" +
                               f"Дата: {data_event['Дата']} \n" +
                               f"Время: {data_event['Время']}")
    # Запись события в базу
    write_event_to_base_query = f"INSERT INTO 'event_from_users' ([id],[user_name],[first_name],[date_time],[event]) " \
                                f"VALUES ('{user_info['id']}','{user_info['Имя пользователя']}','{user_info['Имя']}'," \
                                f"'{data_event['Дата'] + data_event['Время']}','{data_event['Название']}');"
    write_event = base_query(write_event_to_base_query)
    # Проверка корректности тоработки функции
    if write_event is not None:
        print('Событие добавлено успешно')
        await rem_bot.send_message(message.chat.id, 'Событие добавлено.')
    else:
        print('Ошибка записи')
        await rem_bot.send_message(message.chat.id, 'Оп! Что-то с базой не так.')
    await state.finish()  # Завершение работы МС

# Стартовое сообщение
@disp.message_handler(commands=['start'])
async def welcome(message:types.Message):
    await rem_bot.send_message(message.chat.id, 'Привет! Это бот - напоминалка\n' +
                                            'Для взаимодействия используйте кнопки снизу\n' +
                                            'Вызов помощи "/help"')

    # Получение информации о пользователе запустившем бот.
    date = message.date.strftime('%Y-%m-%d %H:%M:%S')
    user_info = {'id': message.from_user.id,
                 'Имя': message.from_user.first_name,
                 'Имя пользователя': message.from_user.username,
                 'Дата': date}
    print(user_info)

    # Проверка на наличие пользователя в базе
    # Есть - хорошо, нету - добавить.
    query_user_in_base = f"SELECT * FROM 'users' WHERE [id] = {user_info['id']}"  # Запрос на поиск id пользователя
    if base_query(query_user_in_base, mode='search'):
        await rem_bot.send_message(message.chat.id, f"Привет, {user_info['Имя']}, я помню тебя.")
    else:
        # Добавление пользователя в базу
        await rem_bot.send_message(message.chat.id, f"Привет, {user_info['Имя']}, я вижу тебя впервые, но запомню.")
        query_user_insert = f"INSERT INTO 'users' ([id],[first_name],[username],[date]) " \
                            f"VALUES ('{user_info['id']}','{user_info['Имя']}'," \
                            f"'{user_info['Имя пользователя']}','{user_info['Дата']}');"
        if base_query(query_user_insert):
            print('Добавлен новый пользователь')
    user_info.clear()  # Очистка словаря с данными пользователя

    # Создание кнопок интерфейса бота
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Создание объекта клавиатура
    btn_create_event = types.KeyboardButton('Добавить событие')  # Кнопка создания нового события
    btn_my_event = types.KeyboardButton('Показать мои события')  # Кнопка просмотра активных событий пользователя
    btn_event_edit = types.KeyboardButton('Редактировать события') # Кнопка редактирования активных событий пользователя
    markup.row(btn_create_event, btn_my_event)  # Добавление кнопок в первый ряд
    markup.row(btn_event_edit)  # Добавление кнопок во второй ряд
    await rem_bot.send_message(message.chat.id, 'Кнопки появятся ниже', reply_markup=markup)

# Функция принятия сообщения от пользователя (реакция нажатия на кнопки "Показать мои события")
@disp.message_handler(lambda message: message.text == 'Показать мои события')
async def my_events_command(message:types.Message):
    user = message.from_user.id  # получаем имя пользователя
    query = f"SELECT * FROM 'event_from_users' WHERE [id] = {user}"  # Запрос на поиск событий в базе
    user_events = base_query(query, mode='search')
    if user_events:
        print(user_events)
        await rem_bot.send_message(message.chat.id, user_events)
    else:
        print('Записей нет.')
        await rem_bot.send_message(message.chat.id, 'Записей нет.')

# Функция принятия сообщения от пользователя (реакция нажатия на кнопки "Редактировать события")
@disp.message_handler(lambda message: message.text == 'Редактировать события')
async def edit_events_command(message:types.Message):
    await rem_bot.send_message(message.chat.id, 'Тут будет сложный код =)')
    # Дописать сложный код редактирования событий

"""
    # Запись события в базу
    write_event_to_base_query = f"INSERT INTO 'event_from_users' ([id],[user_name],[first_name],[date_time],[event]) " \
                                f"VALUES ('{temp_event['id']}','{temp_event['Имя']}','{temp_event['Имя пользователя']}'," \
                                f"'{temp_event['date'] + '' +  '' + temp_event['time']}','{temp_event['name']}');"
    write_event = base_query(write_event_to_base_query)
    # Проверка корректности тоработки функции
    if write_event is not None:
        print('Событие добавлено успешно')
        rem_bot.send_message(messege.chat.id, 'Событие добавлено.')
    else:
        print('Ошибка записи')
        rem_bot.send_message(messege.chat.id, 'Оп! Что-то с базой не так.')
    temp_event.clear() # Очистка временного массива с данными о событии
"""

# Фоновая функция
async def cickle_func():
    print('Запуск фоновой функции')
    while True:
        print('Фоновая функция работает')
        await asyncio.sleep(5)


if __name__ == '__main__':
    disp.loop.create_task(cickle_func())
    executor.start_polling(disp, skip_updates=True)


"""
Старый код c pytelegramBotAPI
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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)        # Создание объекта клавиатура
    btn_create_event = types.KeyboardButton('Добавить событие')     # Кнопка создания нового события
    btn_my_event = types.KeyboardButton('Показать мои события')     # Кнопка просмотра активных событий пользователя
    btn_event_edit = types.KeyboardButton('Редактировать события')  # Кнопка редактирования активных событий пользователя
    markup.row(btn_create_event, btn_my_event)          # Добавление кнопок в первый ряд
    markup.row(btn_event_edit)                          # Добавление кнопок во второй ряд
    rem_bot.send_message(messege.chat.id, 'Кнопки появятся ниже', reply_markup=markup)

# Функация принятия сообщения от пользователя(реакция нажатия на кнопки)
@rem_bot.message_handler(func=lambda messege: True)
def comand_to_bot(messege):
    # Проверка типа сообщения
    if messege.chat.type == 'private':
        if messege.text == 'Добавить событие':
            event_from_user(messege)

            # Написать функцию создания события
        elif messege.text == 'Показать мои события':
            user = messege.from_user.id                                      # получаем имя пользователя
            query = f"SELECT * FROM 'event_from_users' WHERE [id] = {user}"  # Запрос на поиск событий в базе
            user_events = base_query(query, mode='search')
            if user_events:
                print(user_events)
            else:
                print('Записей нет.')
                rem_bot.send_message(messege.chat.id, 'Записей нет.')
        elif messege.text == 'Редактировать события':
            rem_bot.send_message(messege.chat.id, 'Тут будет сложный код =)')
            # Дописать сложный код редактирования событий

# Функция получения события от пользователя
temp_event = {}
def event_from_user(messege):
    mess = rem_bot.send_message(messege.chat.id, 'Название события')
    rem_bot.register_next_step_handler(mess, event_name_func)

# Функция получения названия события
def event_name_func(messege):
    temp_event['name'] = messege.text
    mess1 = rem_bot.send_message(messege.chat.id, 'Дата события в формате: ГГГГ-ММ-ДД')
    rem_bot.register_next_step_handler(mess1, event_date_func)

# Функция получения даты события
def event_date_func(messege):
    temp_event['date'] = messege.text
    mess2 = rem_bot.send_message(messege.chat.id, 'Время события в фотмате: ЧЧ-ММ')
    rem_bot.register_next_step_handler(mess2, event_time_func)

# Функция получения времени события
def event_time_func(messege):
    temp_event['time'] = messege.text
    rem_bot.send_message(messege.chat.id, 'Событие создано!')
    rem_bot.send_message(messege.chat.id, 'Событие: ' + temp_event['name'] + '\n' +
                         'Дата: ' + temp_event['date'] + '\n' +
                         'Время: ' + temp_event['time'])
    temp_event['Имя'] = messege.from_user.first_name
    temp_event['Имя пользователя'] = messege.from_user.username
    temp_event['id'] = messege.from_user.id
    # Запись события в базу
    write_event_to_base_query = f"INSERT INTO 'event_from_users' ([id],[user_name],[first_name],[date_time],[event]) " \
                                f"VALUES ('{temp_event['id']}','{temp_event['Имя']}','{temp_event['Имя пользователя']}'," \
                                f"'{temp_event['date'] + '' +  '' + temp_event['time']}','{temp_event['name']}');"
    write_event = base_query(write_event_to_base_query)
    # Проверка корректности тоработки функции
    if write_event is not None:
        print('Событие добавлено успешно')
        rem_bot.send_message(messege.chat.id, 'Событие добавлено.')
    else:
        print('Ошибка записи')
        rem_bot.send_message(messege.chat.id, 'Оп! Что-то с базой не так.')
    temp_event.clear() # Очистка временного массива с данными о событии

# Опрос сервера, не написал ли кто-нибудь?"""
#rem_bot.polling(none_stop=True, interval=0)
