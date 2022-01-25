import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext             # импорт библиотеки с машиной состояний
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from back import *


# Запуск
tok = open('TOKEN.txt', 'r')
TOKEN = tok.read()
tok.close()

# Инициализация бота
rem_bot = Bot(token=TOKEN)       # Создание экземпляра бота
loop = asyncio.get_event_loop()       # Создание цикла
disp = Dispatcher(rem_bot, loop=loop, storage=MemoryStorage()) # Добавление цикла в диспетчер,
                                                               # Он запустит полинг и цикл с нашей функцией параллельно.
# Информационное сообщение в консоль
if rem_bot:
    print('Запущено.')
else:
    print('Ошибка запуска.')

# Глобальные переменные
user_events_glob = []

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

# Выход из состояний (отмена для диалога ввода даты)
# "*" - любое состояние МС
@disp.message_handler(state="*", commands='отмена')  # хэндлер срабатывает по команде /отмена
@disp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()  # Получаем текущее состояние МС
    # Если МС не задействована, то ничего не происходит
    if current_state is None:
        return
    await state.finish()
    await message.answer('Ok')

# Ловим название события
@disp.message_handler(state=FSM_event_user.name)
async def event_name(message: types.Message, state: FSMContext):
    # Дописать функцию проверки одинаковых событий (по названию)
    async with state.proxy() as data:               # Узнать что это (вроде запись данных)
        data['Название'] = message.text             # получение данных от пользователя в словарь
    await FSM_event_user.next()                     # Переход к следующему состоянию машины
    await FSM_event_user.date.set()                 # Установка к следующего состоянию машины
    await rem_bot.send_message(message.chat.id, 'Введите дату в формате ГГГГ-ММ-ДД')  # Сообщению пользователю что делать дальше

# Ловим дату события
@disp.message_handler(state=FSM_event_user.date)
async def event_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:          # Узнать что это (вроде запись данных)
        # Проверка даты
        date_input = check_date(message.text)  # Основная функция проверки
        if date_input[0]:
            data['Дата'] = message.text        # Получение данных от пользователя в словарь
            await FSM_event_user.next()        # Переход к следующему состоянию машины
            await FSM_event_user.time.set()    # Установка к следующего состоянию машины
            await rem_bot.send_message(message.chat.id, 'Введите время')  # Сообщению пользователю что делать дальше
            print(date_input[1])
        else:
            print(date_input[1])
            await rem_bot.send_message(message.chat.id, date_input[1])
            await rem_bot.send_message(message.chat.id, 'Введите дату снова\n' + 'Формат даты: ГГГГ-ММ-ДД')

# Завершение диалога
@disp.message_handler(state=FSM_event_user.time)
async def event_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # дописать маску и проверку ввода
        data['Время'] = message.text
        # Словарь с данными пользователя
        user_info = {'id': message.from_user.id,
                     'Имя': message.from_user.first_name,
                     'Имя пользователя': message.from_user.username}

        data_event = data.as_dict()   # Данные в памяти в виде словаря
    await rem_bot.send_message(message.chat.id, 'Событие: \n' +
                               f"Пользователь: {user_info['Имя']} \n" +
                               f"Название: {data_event['Название']} \n" +
                               f"Дата: {data_event['Дата']} \n" +
                               f"Время: {data_event['Время']}")
    # Запись события в базу
    write_event_to_base_query = f"INSERT INTO 'event_from_users' ([id],[user_name],[first_name],[date_time],[event]) " \
                                f"VALUES ('{user_info['id']}','{user_info['Имя пользователя']}','{user_info['Имя']}'," \
                                f"'{data_event['Дата'] + ' ' + data_event['Время']}','{data_event['Название']}');"
    write_event = base_query(write_event_to_base_query)
    # Проверка корректности отработки функции
    if write_event is not None:
        print('Событие добавлено успешно')
        await rem_bot.send_message(message.chat.id, 'Событие добавлено.')
    else:
        print('Ошибка записи')
        await rem_bot.send_message(message.chat.id, 'Оп! Что-то с базой не так.')
    await state.finish()  # Завершение работы МС

######################################################################################################################

# Кнопка "Редактировать события" через FSM
class FSM_edit_event(StatesGroup):
    event_keyboard = State()       # Состояние отображение списка собылий в виду кнопок
    event_edit = State()           # Сотояние редактирования событий
    event_new_name = State()       # Состояние получения нового имени
    event_new_date = State()       # Состояние получения новой даты
    event_new_time = State()       # Cостояние получения пового времени


# Начало работы редактирования
@disp.message_handler(lambda message: message.text == 'Редактировать события', state=None)
async def edit_events_command(message:types.Message):
    await FSM_edit_event.event_keyboard.set()     # Установка нового состояния МС

    # Работа функции
    user = message.from_user.id  # получаем имя пользователя
    query = f"SELECT * FROM 'event_from_users' WHERE [id] = {user}"  # Запрос на поиск событий в базе
    global user_events_glob
    user_events_glob.clear()                                   # Очистка глобального массива событий
    data_from_query = base_query(query, mode='search')
    # Проверка на ошибку БД
    if data_from_query is not None:
        user_events_glob.extend(data_from_query)  # Передача массива с событиями в глобальную переменную
    else:
        await rem_bot.send_message(message.chat.id, 'Ооп! Ошибкочка с базой.')
        print('Ошибка с БД')

    # Инлайновая клавиатура обработки событий.
    # Массив кнопок с названиями событий
    button_mass = []
    for line in user_events_glob:
        button_mass.append(InlineKeyboardButton(text=f'{line[4]}', callback_data=f'users_events_button{line[4]}'))

    # Создание клавиатуры
    inline_key = InlineKeyboardMarkup(row_width=2) # Создание объекта клавиатуры, в ряд 2 кнопки
    inline_key.add(*button_mass)                   # добавление массива кнопок в объект клавиатуры
    inline_key.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))
    await message.answer('События в кнопках', reply_markup=inline_key)

# Кнопка отмены редактирования
@disp.callback_query_handler(Text(startswith='cancel'), state='*') # хэндлер срабатывает по команде /отмена
async def cancel_handler(callback : types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()  # Получаем текущее состояние МС
    # Если МС не задействована, то ничего не происходит
    if current_state is None:
        return

    await callback.message.answer('Редактирование отменено')  # Вывод пользователю
    await callback.answer()
    await state.finish()

# Обработчик события(обновления) имя записанное в callback_data
@disp.callback_query_handler(Text(startswith='users_events_button'), state=FSM_edit_event.event_keyboard)
async def edit_events_button(callback : types.CallbackQuery):
    await FSM_edit_event.next()
    await FSM_edit_event.event_edit.set()
    event = callback.data.replace('users_events_button','')  # Вытягиваем название события
    # Инлайновая клавиатура обработки событий.
    inline_key = InlineKeyboardMarkup(row_width=2)  # Создание объекта клавиатуры, в ряд 2 кнопки
    edit_button = InlineKeyboardButton(text='Редактировать', callback_data='click_edit')  # Кнопка редактировать
    cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel')  # Кнопка отмена
    inline_key.add(edit_button, cancel_button)

    for line in user_events_glob:
        if event in line:
            await callback.message.answer('Событие: ' + f'{line[4]}\n' +
                                          'Дата: ' + f'{line[3]}', reply_markup=inline_key)  # Вывод пользователю
            break
    else:
        print('Ошибка при поиске события')   # Отладочная строка этот else может никогда не сработать, подумать и убрать после отладки

    await callback.answer()   # Ответ на коллбэк (ответ должен быть обязательно)
                              # Это убирает часики ожидания на кнопке

# Начало диалога для получения новых данных нового имени события
@disp.callback_query_handler(Text(startswith='click_edit'), state=FSM_edit_event.event_edit)
async def edit_current_event(callback : types.CallbackQuery):
    await callback.message.answer('Введите новое имя события.')
    await FSM_edit_event.next()
    await FSM_edit_event.event_new_name.set()
    await callback.answer()

# Получение нового имени
@ disp.message_handler(state=FSM_edit_event.event_new_name)
async def edit_name(message : types.Message, state : FSMContext):
    async with state.proxy() as data:
        data['Новое имя события'] = message.text
    await rem_bot.send_message(message.chat.id, 'Введите новую дату в формате: ГГГГ-ММ-ДД')
    await FSM_edit_event.next()
    await FSM_edit_event.event_new_date.set()

# Получение новой даты
@disp.message_handler(state=FSM_edit_event.event_new_date)
async def edit_date(message:types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['Новая дата события'] = message.text
    await rem_bot.send_message(message.chat.id, 'Введите новое время в формате: ЧЧ-ММ')
    await FSM_edit_event.next()
    await FSM_edit_event.event_new_time.set()

# Получение нового времени
@disp.message_handler(state=FSM_edit_event.event_new_time)
async def edit_time(message:types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['Новое веремя'] = message.text
    data = data.as_dict()
    print(data)
    # дописать внесение изменений в базу
    await rem_bot.send_message(message.chat.id, 'Событие успешно изменено')
    await state.finish()


#####################################################################################################################

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

# Хелп
@disp.message_handler(commands=['help'])
async def help(message:types.Message):
    await rem_bot.send_message(message.chat.id, 'Как с ним общаться:\n' +
                               '/start перезапуск\n' +
                               'Кнопка "Добавить событие" - добавить новое событие\n' +
                               'Кнопка "Показать мои события" - показывает все активные события пользователя запустившего бот\n' +
                               'Кнопка "Редактировать события" - открывает менюшку редактирования событий')

# Функция принятия сообщения от пользователя (реакция нажатия на кнопки "Показать мои события")
@disp.message_handler(lambda message: message.text == 'Показать мои события')
async def my_events_command(message:types.Message):
    user = message.from_user.id  # получаем имя пользователя
    query = f"SELECT * FROM 'event_from_users' WHERE [id] = {user}"  # Запрос на поиск событий в базе
    user_events = base_query(query, mode='search')
    if user_events:
        for element in user_events:
            await rem_bot.send_message(message.chat.id, f'{element[3]} {element[4]}')
        await rem_bot.send_message(message.chat.id, f'Всего {len(user_events)} событий.')
    else:
        print('Записей нет.')
        await rem_bot.send_message(message.chat.id, 'Записей нет.')


# Фоновая функция
async def cickle_func():
    print('Запуск фоновой функции')
    while True:
        print('Фоновая функция работает')
        await asyncio.sleep(20)

if __name__ == '__main__':
    disp.loop.create_task(cickle_func())
    executor.start_polling(disp, skip_updates=True)
