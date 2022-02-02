import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext             # импорт библиотеки с машиной состояний
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from back import *

#######################################  ИНИЦИАЛИЗАЦИЯ  ########################################################
# Получение токена
tok = open('TOKEN.txt', 'r')
TOKEN = tok.read()
tok.close()

# Инициализация бота
rem_bot = Bot(token=TOKEN)         # Создание экземпляра бота
loop = asyncio.get_event_loop()    # Создание цикла
disp = Dispatcher(rem_bot, loop=loop, storage=MemoryStorage()) # Добавление цикла в диспетчер,
                                                               # Он запустит полинг и цикл с нашей функцией параллельно.

# Функция начала работы бота, сообщение, запуск в полинге
async def start_func(_):
    print('Бот запущен')
    global base, cursor
    base, cursor = start_base()          # Подключение к БД

# Функция завершения работы бота, сообщение, запуск в полинге
# Стабильно работает на Windows 10, на Windows 7 не отрабатывает.
async def stop_func(_):
    print('Бот остановлен')
    global base, cursor
    stop_base(base, cursor)

# Глобальные переменные
user_events_glob = []

# Функция нулевого вопроса
def zero_digit(gidit):
    out = f"0{gidit}"
    return out
#######################################  ИНИЦИАЛИЗАЦИЯ  ###############################################################

######################################## ФУНКЦИЯ ОТСЛЕЖИВАНИЯ СОБЫТИЙ #################################################
# Фоновая функция отслеживания событий
async def reminer_func():
    now_time = datetime.datetime.now().strftime('%H-%M-%S')  # Текущее время
    now_date = datetime.datetime.now().strftime('%Y-%m-%d')  # Текущая дата
    now_time_mass = list(map(int, now_time.split('-')))
    second = (60 - int(now_time_mass[2])) + 1
    # Стабильный запуск, base и cursor успеют определиться
    if second < 5:
        second = 5
    # Запуск в начале любой минуты
    while True:
        await asyncio.sleep(second)
        break
    print('Запуск фоновой функции')
    while True:
        now_time = datetime.datetime.now().strftime('%H-%M-%S')  # Текущее время
        global base, cursor
        query = f"SELECT id, user_name, event, status FROM 'event_from_users' " \
                f"WHERE [date] = '{now_date}' AND [time] = '{now_time[:-3]}'"
        # Получение событий из базы
        event_mass = base_query(base=base, cursor=cursor, query=query, mode='search')
        # Отсылка событий по одному
        for line in event_mass:
            if line[3] != 'done':
                print('Напоминание отправлено', line)
                await rem_bot.send_message(line[0], f'Напоминание: {line[2]}')    # Отсылка сообщения пользователю
                query = f"UPDATE 'event_from_users' SET [status] = 'done' " \
                        f"WHERE [id] = {line[0]} AND [event] = '{line[2]}';"
                base_query(base=base, cursor=cursor, query=query)
                # Запись в журнал
                time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')  # Текущая дата и время
                name_query = f"SELECT first_name FROM 'users' WHERE [id] = {line[0]}"
                user_name = base_query(base=base, cursor=cursor, query=name_query, mode='search')
                log_query = f"INSERT INTO 'log' ([id], [first_name], [event], [action], [time])" \
                        f"VALUES ({line[0]}, '{user_name[0][0]}','{line[2]}', 'done', '{time_now}')"
                base_query(base=base, cursor=cursor, query=log_query)  # Отметка в журнале

        event_mass.clear()
        await asyncio.sleep(50)  # Задержка опроса базы

######################################## ФУНКЦИЯ ОТСЛЕЖИВАНИЯ СОБЫТИЙ #################################################

########################################## СОЗДАНИЕ ###################################################################
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
@disp.message_handler(commands=['отмена'], state="*")  # хэндлер срабатывает по команде /отмена
@disp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()  # Получаем текущее состояние МС
    # Если МС не задействована, то ничего не происходит
    if current_state is None:
        return
    await state.finish()
    await message.answer('Oтмена')

# Ловим название события
@disp.message_handler(state=FSM_event_user.name)
async def event_name(message: types.Message, state: FSMContext):
    id = message.from_user.id                           # id пользователя
    if repeat_name(message.text.lower(), id, base=base, cursor=cursor):
        async with state.proxy() as data:               # Узнать что это (вроде запись данных)
            data['Название'] = message.text.lower()     # получение данных от пользователя в словарь
        await FSM_event_user.next()                     # Переход к следующему состоянию машины
        await FSM_event_user.date.set()                 # Установка к следующего состоянию машины
        await rem_bot.send_message(message.chat.id, 'Введите дату в формате ГГГГ-ММ-ДД')  # Сообщению пользователю что делать дальше
    else:
        await message.reply('Такое событие уже есть. Придумайте другое название.')

# Ловим дату события
@disp.message_handler(state=FSM_event_user.date)
async def event_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:          # Узнать что это (вроде запись данных)
        # Проверка даты
        date_input = check_date(message.text)  # Основная функция проверки
        if date_input[0]:
            # Решение с форматом даты 2022-02-05 2022-2-5
            date_mass = message.text.split('-')
            if int(date_mass[1]) < 10 and len(date_mass[1]) < 2:
                date_mass[1] = f"0{date_mass[1]}"
            if int(date_mass[2]) < 10 and len(date_mass[2]) < 2:
                date_mass[2] = f"0{date_mass[2]}"
            data['Дата'] = f"{date_mass[0]}-{date_mass[1]}-{date_mass[2]}"        # Получение данных от пользователя в словарь
            await FSM_event_user.next()        # Переход к следующему состоянию машины
            await FSM_event_user.time.set()    # Установка к следующего состоянию машины
            await rem_bot.send_message(message.chat.id, 'Введите время')  # Сообщению пользователю что делать дальше
        else:
            await rem_bot.send_message(message.chat.id, date_input[1])
            await rem_bot.send_message(message.chat.id, 'Введите дату снова\n' + 'Формат даты: ГГГГ-ММ-ДД')

# Завершение диалога
@disp.message_handler(state=FSM_event_user.time)
async def event_time(message: types.Message, state: FSMContext):
    # Словарь с данными пользователя
    user_info = {'id': message.from_user.id,
                 'Имя': message.from_user.first_name,
                 'Имя пользователя': message.from_user.username}
    async with state.proxy() as data:
        time_input = check_time(message.text, str(data['Дата']))  # Проверка времени на корректность
        if time_input[0]:
            # Добавление 0, формат 09-23 вместо 9-23
            time_mass = message.text.split('-')
            if int(time_mass[0]) < 10:
                time_mass[0] = f'0{time_mass[0]}'
                data['Время'] = f"{time_mass[0]}-{time_mass[1]}"
            else:
                data['Время'] = message.text

            data_event = data.as_dict()   # Данные в памяти в виде словаря
            await rem_bot.send_message(message.chat.id, 'Событие: \n' +
                               f"Пользователь: {user_info['Имя']} \n" +
                               f"Название: {data_event['Название']} \n" +
                               f"Дата: {data_event['Дата']} \n" +
                               f"Время: {data_event['Время']}")
            # Запись события в базу
            write_event_to_base_query = f"INSERT INTO 'event_from_users' ([id],[user_name],[first_name],[date],[time],[event],[status]) " \
                                f"VALUES ('{user_info['id']}','{user_info['Имя пользователя']}','{user_info['Имя']}'," \
                                f"'{data_event['Дата']}','{data_event['Время']}','{data_event['Название']}','wait');"
            write_event = base_query(base=base, cursor=cursor, query=write_event_to_base_query)
            # Запись в журнал
            time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')  # Текущая дата и время
            log_query = f"INSERT INTO 'log' ([id], [first_name], [event], [action], [time])" \
                        f"VALUES ({user_info['id']}, '{user_info['Имя']}','{data_event['Название']}', 'create', '{time_now}')"
            base_query(base=base, cursor=cursor, query=log_query)  # Отметка в журнале
            # Проверка корректности отработки функции
            if write_event is not None:
                await rem_bot.send_message(message.chat.id, 'Событие добавлено.')
            else:
                await rem_bot.send_message(message.chat.id, 'Оп! Что-то с базой не так.')
            await state.finish()  # Завершение работы МС
        else:
            await message.reply(time_input[1])
            await rem_bot.send_message(message.chat.id, 'Введите время снова ЧЧ-ММ.')

############################################ СОЗДАНИЕ #################################################################

######################################## РЕДАКТИРОВАНИЕ ###############################################################

# Кнопка "Редактировать события" через FSM
class FSM_edit_event(StatesGroup):
    event_keyboard = State()       # Состояние отображение списка собылий в виду кнопок
    event_edit = State()           # Состояние редактирования событий
    event_new_name = State()       # Состояние получения нового имени
    event_new_date = State()       # Состояние получения новой даты
    event_new_time = State()       # Cостояние получения нового времени

# Начало работы редактирования
@disp.message_handler(lambda message: message.text == 'Редактировать события', state=None)
async def edit_events_command(message:types.Message, state:FSMContext):
    await FSM_edit_event.event_keyboard.set()     # Установка нового состояния МС
    # Работа функции
    user = message.from_user.id  # получаем имя пользователя
    async with state.proxy() as data:
        data['id'] = user
    query = f"SELECT * FROM 'event_from_users' WHERE [id] = {user}"  # Запрос на поиск событий в базе
    global user_events_glob
    user_events_glob.clear()                                   # Очистка глобального массива событий
    data_from_query = base_query(base=base, cursor=cursor, query=query, mode='search')
    # Проверка на ошибку БД
    if data_from_query is not None:
        user_events_glob.extend(data_from_query)  # Передача массива с событиями в глобальную переменную
    else:
        await rem_bot.send_message(message.chat.id, 'Ооп! Ошибочка с базой.')
        print('Ошибка с БД при редактировании события')

    # Инлайновая клавиатура обработки событий.
    # Массив кнопок с названиями событий
    button_mass = []
    for line in user_events_glob:
        button_mass.append(InlineKeyboardButton(text=f'{line[5]}', callback_data=f'users_events_button{line[5]}'))

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

    await callback.message.answer('Отменено')  # Вывод пользователю
    await callback.answer()
    await state.finish()

# Обработчик события(обновления) имя записанное в callback_data
@disp.callback_query_handler(Text(startswith='users_events_button'), state=FSM_edit_event.event_keyboard)
async def edit_events_button(callback : types.CallbackQuery, state:FSMContext):
    event = callback.data.replace('users_events_button', '').lower()  # Вытягиваем название события
    async with state.proxy() as data:
        data['Старое имя события'] = event
    await FSM_edit_event.next()
    await FSM_edit_event.event_edit.set()
    # Инлайновая клавиатура обработки событий.
    inline_key = InlineKeyboardMarkup(row_width=2)  # Создание объекта клавиатуры, в ряд 2 кнопки
    edit_button = InlineKeyboardButton(text='Редактировать', callback_data='click_edit')  # Кнопка редактировать
    cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel')  # Кнопка отмена
    inline_key.add(edit_button, cancel_button)
    # Вывод пользователю
    for line in user_events_glob:
        if event in line:
            await callback.message.answer('Событие: ' + f'{line[5]}\n' +
                                          'Дата: ' + f'{line[3]}\n' +
                                          'Время: ' + f'{line[4]}', reply_markup=inline_key)
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
        old_name = data['Старое имя события']
    # События или нет в базе или пользователь оставляет старое имя
    if repeat_name(message.text.lower(), message.from_user.id, base=base, cursor=cursor) or old_name == message.text.lower():
        async with state.proxy() as data:
            data['Новое имя события'] = message.text.lower()
        await rem_bot.send_message(message.chat.id, 'Введите новую дату в формате: ГГГГ-ММ-ДД')
        await FSM_edit_event.next()
        await FSM_edit_event.event_new_date.set()
    else:
        await message.reply('Такое событие уже есть. Придумайте новое имя.')

# Получение новой даты
@disp.message_handler(state=FSM_edit_event.event_new_date)
async def edit_date(message:types.Message, state:FSMContext):
    new_date = check_date(message.text)  # Проверка корректности даты
    if new_date[0]:
        # Решение с форматом даты 2022-02-05 2022-2-5
        date_mass = message.text.split('-')
        if int(date_mass[1]) < 10 and len(date_mass[1]) < 2:
            date_mass[1] = f"0{date_mass[1]}"
        if int(date_mass[2]) < 10 and len(date_mass[2]) < 2:
            date_mass[2] = f"0{date_mass[2]}"
            async with state.proxy() as data:
                data['Новая дата события'] = f"{date_mass[0]}-{date_mass[1]}-{date_mass[2]}"
        await rem_bot.send_message(message.chat.id, 'Введите новое время в формате: ЧЧ-ММ')
        await FSM_edit_event.next()
        await FSM_edit_event.event_new_time.set()
    else:
        await message.reply(new_date[1])
        await rem_bot.send_message(message.chat.id, 'Введите дату снова.')

# Получение нового времени
@disp.message_handler(state=FSM_edit_event.event_new_time)
async def edit_time(message:types.Message, state:FSMContext):
    # Дописать проверку
    flag = False # Флаг чтобы убрать множественную не понятную вложенность
    async with state.proxy() as data:
        new_time = check_time(message.text, data['Новая дата события'])
        if new_time[0]:
            data['Новое время'] = message.text
            data = data.as_dict()
            replace_query = f"UPDATE 'event_from_users' SET [date] = '{data['Новая дата события']}'," \
                            f"[time] = '{data['Новое время']}'," \
                            f"[event] = '{data['Новое имя события']}'" \
                            f"WHERE [id] = {data['id']} AND [event] = '{data['Старое имя события']}';"
            flag = base_query(base=base, cursor=cursor, query=replace_query)
            # Запись в журнал
            time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')  # Текущая дата и время
            name_query = f"SELECT first_name FROM 'users' WHERE [id] = {data['id']}"
            user_name = base_query(base=base, cursor=cursor, query=name_query, mode='search')
            log_query = f"INSERT INTO 'log' ([id], [first_name], [event], [action], [time])" \
                        f"VALUES ({data['id']}, '{user_name[0][0]}'," \
                        f"'{data['Старое имя события']} {'>'} {data['Новое имя события']}', 'edit', '{time_now}')"
            base_query(base=base, cursor=cursor, query=log_query)  # Отметка в журнале
        else:
            await message.reply(new_time[1])
            await rem_bot.send_message(message.chat.id, 'Введите время снова.')

    if flag:
        await rem_bot.send_message(message.chat.id, 'Событие успешно изменено')
        await rem_bot.send_message(message.chat.id, f"Событие: {data['Новое имя события']}\n"
                                                    f"Дата: {data['Новая дата события']}\n"
                                                    f"Время: {data['Новое время']}")
        print('Замена произведена успешно')
        await state.finish()
    else:
        print('Ошибка при замене события')

######################################## РЕДАКТИРОВАНИЕ ###############################################################

####################################### УДАЛЕНИЕ СОБЫТИЯ ##############################################################
# Кнопка "Удалить событие" через FSM
class FSM_delete_event(StatesGroup):
    event_keyboard = State()       # Состояние отображение списка событий в виде кнопок
    event_delete = State()         # Состояние удаления событий

# Функция кнопки "Удалить событие"
@disp.message_handler(lambda message: message.text == 'Удалить событие', state=None)
async def show_event(message:types.Message, state:FSMContext):
    await FSM_delete_event.event_keyboard.set()                      # Установка нового состояния МС
    user = message.from_user.id                                      # Получаем имя пользователя
    query = f"SELECT * FROM 'event_from_users' WHERE [id] = {user}"  # Запрос на поиск событий в базе
    async with state.proxy() as data:
        data['id'] = user
    global user_events_glob
    user_events_glob.clear()                                   # Очистка глобального массива событий
    data_from_query = base_query(base=base, cursor=cursor, query=query, mode='search')
    # Проверка на корректную отработку запроса в БД
    if data_from_query is not None:
        user_events_glob.extend(data_from_query)  # Передача массива с событиями в глобальную переменную
    else:
        await rem_bot.send_message(message.chat.id, 'Ооп! Ошибочка с базой.')
        print('Ошибка с БД при удалении')

    # Инлайновая клавиатура обработки событий.
    # Массив кнопок с названиями событий
    if data_from_query:
        button_mass = []
        for line in user_events_glob:
            button_mass.append(InlineKeyboardButton(text=f'{line[5]}', callback_data=f'users_events_button{line[5]}'))

        # Создание клавиатуры
        inline_key = InlineKeyboardMarkup(row_width=2)  # Создание объекта клавиатуры, в ряд 2 кнопки
        inline_key.add(*button_mass)                    # добавление массива кнопок в объект клавиатуры
        inline_key.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))
        await message.answer('События в кнопках', reply_markup=inline_key)
    else:
        await message.answer('Записей нет')
        await state.finish()

# Подтверждение удаления
@disp.callback_query_handler(Text(startswith='users_events_button'), state=FSM_delete_event.event_keyboard)
async def confirm_delete(callback:types.CallbackQuery, state:FSMContext):
    await FSM_delete_event.next()
    await FSM_delete_event.event_delete.set()
    event = callback.data.replace('users_events_button', '')                # Вытягиваем название события
    async with state.proxy() as data:
        data['Событие'] = event
    query = f"SELECT [date],[time] FROM 'event_from_users' WHERE [event] = '{event}' AND [id] = {data['id']}"
    date = base_query(base=base, cursor=cursor, query=query, mode='search') # Получаем время события
    inline_key = InlineKeyboardMarkup(row_width=2)
    inline_key.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'),  # Кнопка отмена (работает один на всех хэндлер)
                   InlineKeyboardButton(text='Удалить', callback_data='delete')) # Кнопка удалить
    await callback.message.answer(f"Событие: {event}\nДата: {date[0][0]}\nВремя: {date[0][1]}", reply_markup=inline_key)
    await callback.answer()

# Удаление
@disp.callback_query_handler(Text(startswith='delete'), state=FSM_delete_event.event_delete)
async def delete_event(callback:types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        data = data.as_dict()
    delete_query = f"DELETE FROM 'event_from_users' WHERE [event] = '{data['Событие']}' " \
                   f"AND [id] = '{data['id']}' "
    # Запись в журнале
    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')  # Текущая дата и время
    name_query = f"SELECT first_name FROM 'users' WHERE [id] = {data['id']}"
    user_name = base_query(base=base, cursor=cursor, query=name_query, mode='search')
    delete_log_query = f"INSERT INTO 'log' ([id], [first_name], [event], [action], [time])" \
                       f"VALUES ({data['id']},'{user_name[0][0]}','{data['Событие']}','delete', '{time_now}')"
    base_query(base=base, cursor=cursor, query=delete_log_query)

    if base_query(base=base, cursor=cursor, query=delete_query):
        print(f"Событие {data['Событие']} удалено пользователь: {user_name[0][0]}")
        await callback.message.answer(f"Удалено событие: {data['Событие']}")
    else:
        await callback.message.answer('Ооп! Ошибочка! Удаление не сработало.')
        print('ошибка удаления из базы')
    await callback.answer()
    await state.finish()

####################################### УДАЛЕНИЕ СОБЫТИЯ ##############################################################
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

    # Проверка на наличие пользователя в базе
    # Есть - хорошо, нету - добавить.
    query_user_in_base = f"SELECT * FROM 'users' WHERE [id] = {user_info['id']}"  # Запрос на поиск id пользователя
    if base_query(base, cursor, query=query_user_in_base, mode='search'):
        await rem_bot.send_message(message.chat.id, f"Привет, {user_info['Имя']}, я помню тебя.")
    else:
        # Добавление пользователя в базу
        await rem_bot.send_message(message.chat.id, f"Привет, {user_info['Имя']}, я вижу тебя впервые, но запомню.")
        query_user_insert = f"INSERT INTO 'users' ([id],[first_name],[username],[date]) " \
                            f"VALUES ('{user_info['id']}','{user_info['Имя']}'," \
                            f"'{user_info['Имя пользователя']}','{user_info['Дата']}');"
        if base_query(base=base, cursor=cursor, query=query_user_insert):
            print('Добавлен новый пользователь')
            print(user_info)
    user_info.clear()  # Очистка словаря с данными пользователя

    # Создание кнопок интерфейса бота
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)       # Создание объекта клавиатура
    btn_create_event = types.KeyboardButton('Добавить событие')    # Кнопка создания нового события
    btn_my_event = types.KeyboardButton('Показать мои события')    # Кнопка просмотра активных событий пользователя
    btn_event_edit = types.KeyboardButton('Редактировать события') # Кнопка редактирования активных событий пользователя
    btn_delete_event = types.KeyboardButton('Удалить событие')     # Кнопка удаления события
    markup.row(btn_create_event, btn_my_event)            # Добавление кнопок в первый ряд
    markup.row(btn_event_edit, btn_delete_event)          # Добавление кнопок во второй ряд
    await rem_bot.send_message(message.chat.id, 'Кнопки появятся ниже', reply_markup=markup)

# Хелп
@disp.message_handler(commands=['help'])
async def help(message:types.Message):
    await rem_bot.send_message(message.chat.id, 'Как с ним общаться:\n' +
                               '/start перезапуск\n' +
                               'Кнопка "Добавить событие" - добавить новое событие\n' +
                               'Кнопка "Показать мои события" - показывает все активные события пользователя запустившего бот\n' +
                               'Кнопка "Редактировать события" - открывает менюшку редактирования событий\n' +
                               'Кнопка "Удалить событие" - удаляет событие\n' +
                               'Для отмены нажать кнопку отмена, если такой нет, '
                               'то написать в сообщении: отмена')

# Функция кнопки "Показать мои события"
@disp.message_handler(lambda message: message.text == 'Показать мои события')
async def my_events_command(message:types.Message):
    user = message.from_user.id  # получаем имя пользователя
    query = f"SELECT * FROM 'event_from_users' WHERE [id] = {user}"  # Запрос на поиск событий в базе
    user_events = base_query(base, cursor, query=query, mode='search')
    if user_events:
        for element in user_events:
            await rem_bot.send_message(message.chat.id, f'{element[5]} {element[3]} {element[4]}')
        await rem_bot.send_message(message.chat.id, f'Всего {len(user_events)} событий.')
    else:
        await rem_bot.send_message(message.chat.id, 'Записей нет.')

# Запуск
if __name__ == '__main__':
    disp.loop.create_task(reminer_func())
    executor.start_polling(disp, skip_updates=True, on_startup=start_func, on_shutdown=stop_func)
