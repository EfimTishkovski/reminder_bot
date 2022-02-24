import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext             # импорт библиотеки с машиной состояний
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from back import *
from emoji import *
import pytz
from datetime import datetime, timedelta

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

# Глобальные переменные
# base - объект соединения с базой определяется в start_func при запуске
# cursor - объект курсор для работы с базой определяется в start_func при запуске

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

#######################################  ИНИЦИАЛИЗАЦИЯ  ###############################################################

######################################## ФУНКЦИЯ ОТСЛЕЖИВАНИЯ СОБЫТИЙ #################################################
# Фоновая функция отслеживания событий
async def reminer_func():
    now_time = datetime.utcnow().strftime('%d:%m:%Y:%H:%M:%S')  # Текущее время и дата для запуска функции
    now_time_mass = list(map(int, now_time.split(':')))
    second = (60 - int(now_time_mass[5])) + 1
    # Стабильный запуск, base и cursor успеют определиться
    if second < 5:
        second = 5
    # Запуск в начале любой минуты
    while True:
        await asyncio.sleep(second)
        break
    print('Запуск фоновой функции')
    while True:
        now_time = datetime.utcnow().strftime('%d.%m.%Y %H:%M')  # Текущее время и дата
        global base, cursor
        query = f"SELECT id, user_name, event, status FROM 'event_from_users' WHERE [utc] = '{now_time}'"
        # Получение событий из базы
        event_mass = base_query(base=base, cursor=cursor, query=query, mode='search')
        # Отсылка событий по одному
        for line in event_mass:
            if line[3] != 'done':
                # Отправка сообщения пользователю
                await rem_bot.send_message(line[0], f'{police_cars_revolving_light}Напоминание: {line[2]}')
                query = f"UPDATE 'event_from_users' SET [status] = 'done' " \
                        f"WHERE [id] = {line[0]} AND [event] = '{line[2]}';"
                base_query(base=base, cursor=cursor, query=query)
                print('Напоминание отправлено', line)
                # Запись в журнал
                time_now = datetime.now().strftime('%Y-%m-%d %H:%M')  # Текущая дата и время
                name_query = f"SELECT first_name FROM 'users' WHERE [id] = {line[0]}"
                user_name = base_query(base=base, cursor=cursor, query=name_query, mode='search')
                log_query = f"INSERT INTO 'log' ([id], [first_name], [event], [action], [time])" \
                        f"VALUES ({line[0]}, '{user_name[0][0]}','{line[2]}', 'done', '{time_now}')"
                base_query(base=base, cursor=cursor, query=log_query)  # Отметка в журнале

        event_mass.clear()
        await asyncio.sleep(30)  # Задержка опроса базы

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
async def event_start(message: types.Message, state:FSMContext):
    await FSM_event_user.name.set()
    # Открываем прокси и записываем данные пользователя
    us_id = message.from_user.id
    utc_zone_query = f"SELECT time_zone FROM 'users' WHERE [id] = {us_id}"
    user_utc_zone = base_query(base=base, cursor=cursor, query=utc_zone_query, mode='search')
    async with state.proxy() as data:
        data['id'] = us_id
        data['time_zone'] = user_utc_zone[0][0]
    # Образец для пользователя
    await rem_bot.send_message(message.chat.id, f'{heavy_exclamation_mark_symbol}ПРИМЕР')
    await rem_bot.send_message(message.chat.id, f'{heavy_exclamation_mark_symbol}'
                                                f'Напоминание: Что-то очень важное что никак нельзя забыть.\n' +
                                                'Дата: Дата когда об этом нужно напомнить.\n' +
                                                'Время: В какое время напомнить.')
    # Первый запрос
    await rem_bot.send_message(message.chat.id, 'Введите название напоминания')

# Выход из состояний (отмена для диалога ввода даты)
# "*" - любое состояние МС
@disp.message_handler(commands=['отмена', 'cancel'], state="*")  # хэндлер срабатывает по команде /отмена
@disp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
@disp.message_handler(Text(equals='cancel', ignore_case=True), state="*")
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
    id_us = message.from_user.id                    # id пользователя
    # repeat_name() возможно не понадобиться
    if repeat_name(message.text.lower(), id_us, base=base, cursor=cursor):
        await FSM_event_user.next()                 # Переход к следующему состоянию машины
        # Кнопки сегодня и завтра
        inline_key = InlineKeyboardMarkup()
        today_butt = InlineKeyboardButton(text=f'Сегодня', callback_data=f'today')
        tomorrow_butt = InlineKeyboardButton(text=f'Завтра', callback_data=f'tomorrow')
        inline_key.add(today_butt, tomorrow_butt)
        # Сообщению пользователю что делать дальше
        mtu = await rem_bot.send_message(message.chat.id, 'Введите дату в формате ДД.ММ.ГГГГ', reply_markup=inline_key)
        async with state.proxy() as data:
            data['Название'] = message.text.lower()   # Получение данных от пользователя в словарь
            data['Первое сообщение'] = mtu.message_id # Получение id сообщения в словарь
    else:
        await message.reply('Такое событие уже есть. Придумайте другое название.')

# Ловим дату события ввод пользователем
@disp.message_handler(state=FSM_event_user.date)
async def event_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # Удаляем кнопки в предыдущем сообщении
        if data['Первое сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Первое сообщение'],
                                                reply_markup=None)
            data['Первое сообщение'] = False

    async with state.proxy() as data:
        # Проверка даты
        date_input = check_date(message.text)  # Основная функция проверки
        if date_input[0]:
            input_date = date_standrt(message.text)  # Приведение даты к стандартному виду
            zone = pytz.timezone(data['time_zone'])    # Создание объекта часового пояса
            user_loc_date = zone.localize(datetime.strptime(f"{input_date}", '%d.%m.%Y')) # Объект даты от пользователя
            loc_date = datetime.now(pytz.timezone(data['time_zone']))\
                .replace(hour=0, minute=0, second=0, microsecond=0) # Местная локальная дата
            # Проверка на прошлое
            if user_loc_date >= loc_date:
                data['Дата'] = input_date
                await FSM_event_user.next()        # Переход к следующему состоянию машины
                await rem_bot.send_message(message.chat.id, 'Введите время в формате ЧЧ:ММ')  # Сообщению пользователю что делать дальше
            else:
                await message.reply('Дата прошла, введите другую')
        else:
            await rem_bot.send_message(message.chat.id, date_input[1])
            await rem_bot.send_message(message.chat.id, 'Введите дату снова\n' + 'Формат даты: ДД.ММ.ГГГГ')

# Ловим дату если нажата кнопка сегодня
@disp.callback_query_handler(Text(startswith='today'), state=FSM_event_user.date)
async def today_date(callback:types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        # Удаляем кнопки в предыдущем сообщении
        if data['Первое сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Первое сообщение'],
                                                reply_markup=None)
            data['Первое сообщение'] = False
        data['Дата'] = datetime.now(pytz.timezone(data['time_zone'])).strftime('%d.%m.%Y')  # Текущая дата локальная
    await callback.message.answer('Введите время в формате ЧЧ:ММ')
    await callback.answer()
    await FSM_event_user.next()

# Ловим дату если нажата кнопка завтра
@disp.callback_query_handler(Text(startswith='tomorrow'), state=FSM_event_user.date)
async def today_date(callback:types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        # Удаляем кнопки в предыдущем сообщении
        if data['Первое сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Первое сообщение'],
                                                reply_markup=None)
            data['Первое сообщение'] = False
        data_now = datetime.now(pytz.timezone(data['time_zone']))
        data_tomorrow = data_now + timedelta(days=1)
        data['Дата'] = str(data_tomorrow.strftime('%d.%m.%Y'))
    await callback.message.answer('Введите время в формате ЧЧ:ММ')
    await callback.answer()
    await FSM_event_user.next()

# Завершение диалога
@disp.message_handler(state=FSM_event_user.time)
async def event_time(message: types.Message, state: FSMContext):
    # Словарь с данными пользователя
    user_info = {'id': message.from_user.id,
                 'Имя': message.from_user.first_name,
                 'Имя пользователя': message.from_user.username}
    async with state.proxy() as data:
        data_event = data.as_dict()  # Данные в памяти в виде словаря
    time_input = check_time(message.text)  # Проверка времени на корректность
    if time_input[0]:
        # Приведение времени к стандартному формату
        data_event['Время'] = time_standart(message.text)
        # Переводим время в формат UTC
        zone = pytz.timezone(data['time_zone'])  # Создание объекта часового пояса
        # Объект даты от пользователя
        local_time = zone.localize(datetime.strptime(f"{data_event['Дата']} {data_event['Время']}", '%d.%m.%Y %H:%M'))
        local_time_now = datetime.now(zone)
        utc_time_to_base = local_time.astimezone(pytz.utc).strftime('%d.%m.%Y %H:%M') # Значение для записи а базу по шаблону
        # Проверка на прошлое
        if local_time > local_time_now:
            # Послание юзеру, что всё норм
            await rem_bot.send_message(message.chat.id, f'{alarm_cloc}Событие: \n' +
                               f"Пользователь: {user_info['Имя']} \n" +
                               f"Название: {data_event['Название']} \n" +
                               f"Дата: {data_event['Дата']} \n" +
                               f"Время: {data_event['Время']}")
            # Запись события в базу
            id_event = generate_id()   # Генерация id для события
            write_event_to_base_query = f"INSERT INTO 'event_from_users' ([id],[user_name],[first_name],[date],[time]," \
                                        f"[event],[status],[id_event],[UTC]) " \
                                f"VALUES ('{user_info['id']}','{user_info['Имя пользователя']}','{user_info['Имя']}'," \
                                f"'{data_event['Дата']}','{data_event['Время']}','{data_event['Название']}','wait'," \
                                        f"'{id_event}','{utc_time_to_base}');"
            write_event = base_query(base=base, cursor=cursor, query=write_event_to_base_query)
            # Запись в журнал
            time_now = datetime.now().strftime('%d.%m.%Y %H:%M')  # Текущая дата и время
            log_query = f"INSERT INTO 'log' ([id], [first_name], [event], [action], [time])" \
                        f"VALUES ({user_info['id']}, '{user_info['Имя']}','{data_event['Название']}', 'create', '{time_now}')"
            base_query(base=base, cursor=cursor, query=log_query)  # Отметка в журнале
            # Проверка корректности отработки функции
            if write_event is not None:
                await rem_bot.send_message(message.chat.id, 'Событие добавлено.')
                await state.finish()  # Завершение работы МС
            else:
                await rem_bot.send_message(message.chat.id, 'Оп! Что-то с базой не так.')
                await state.finish()  # Завершение работы МС
        elif local_time == local_time_now:
            await rem_bot.send_message(message.chat.id, 'Это прямо сейчас! Действуй! =)')
            await state.finish()  # Завершение работы МС
        else:
            await message.reply('Время прошло, введите время снова ЧЧ:ММ.')
    else:
        await message.reply(time_input[1])
        await rem_bot.send_message(message.chat.id, 'Введите время снова ЧЧ:ММ.')

############################################ СОЗДАНИЕ #################################################################

######################################## РЕДАКТИРОВАНИЕ ###############################################################

# Кнопка "Редактировать события" через FSM
class FSM_edit_event(StatesGroup):
    event_keyboard = State()       # Состояние отображение списка событий в виду кнопок
    event_edit = State()           # Состояние редактирования событий
    event_new_name = State()       # Состояние получения нового имени
    event_new_date = State()       # Состояние получения новой даты
    event_new_time = State()       # Cостояние получения нового времени

# Начало работы редактирования
@disp.message_handler(lambda message: message.text == 'Редактировать события', state=None)
async def edit_events_command(message:types.Message, state:FSMContext):
    user_id = message.from_user.id  # получаем id пользователя
    query = f"SELECT * FROM 'event_from_users' WHERE [id] = {user_id}"  # Запрос на поиск событий в базе
    user_tz_query = f"SELECT time_zone FROM 'users' WHERE [id] = {user_id}"
    user_tz = base_query(base=base, cursor=cursor, query=user_tz_query, mode='search') # Получение временной зоны
    data_from_query = base_query(base=base, cursor=cursor, query=query, mode='search') # Получение событий из базы
    # Проверка на ошибку БД
    button_mass = []
    if data_from_query is not None and user_tz:
        # Массив кнопок с названиями событий
        async with state.proxy() as data:
            for line in data_from_query:
                id_button = line[7]
                button_mass.append(InlineKeyboardButton(text=f'{line[5]}', callback_data=f'ueb{id_button}'))
                data[id_button] = line[5]
            # Создание клавиатуры
            inline_key = InlineKeyboardMarkup(row_width=2)  # Создание объекта клавиатуры, в ряд 2 кнопки
            inline_key.add(*button_mass)  # добавление массива кнопок в объект клавиатуры
            inline_key.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))
            mtu = await message.answer('События в кнопках', reply_markup=inline_key)  # mtu - message to user

        # Сохранение id сообщения и id пользователя, пригодятся дальше
        async with state.proxy() as data:
            data.clear()
            data['id'] = user_id
            data['time_zone'] = user_tz[0][0]
            data['Первое сообщение'] = mtu.message_id
        await FSM_edit_event.event_keyboard.set()  # Установка нового состояния МС
    else:
        await rem_bot.send_message(message.chat.id, 'Ооп! Ошибочка с базой.')
        print('Ошибка с БД при редактировании события')

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
@disp.callback_query_handler(Text(startswith='ueb'), state=FSM_edit_event.event_keyboard)
async def edit_events_button(callback : types.CallbackQuery, state:FSMContext):
    id_event = callback.data.replace('ueb', '')      # Вытягиваем id события
    await FSM_edit_event.next()
    # Инлайновая клавиатура обработки событий.
    inline_key = InlineKeyboardMarkup(row_width=2)  # Создание объекта клавиатуры, в ряд 2 кнопки
    edit_button = InlineKeyboardButton(text='Редактировать', callback_data='click_edit')  # Кнопка редактировать
    cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel')  # Кнопка отмена
    inline_key.add(edit_button, cancel_button)
    # Через запрос в базу
    event_info_query = f"SELECT * FROM 'event_from_users' WHERE [id] = {callback.from_user.id} AND [id_event] = '{id_event}'"
    event_info = base_query(base=base, cursor=cursor, query=event_info_query, mode='search')
    # Вывод пользователю
    if event_info is not None:
        info_to_user = await callback.message.answer(f'{triangular_flag_on_post}Событие: {event_info[0][5]}\n' +
                                          'Дата: ' + f'{event_info[0][3]}\n' +
                                          'Время: ' + f'{event_info[0][4]}', reply_markup=inline_key)
        async with state.proxy() as data:
            data['Имя события'] = event_info[0][5]
            data['Дата'] = event_info[0][3]
            data['Время'] = event_info[0][4]
            data['Второе сообщение'] = info_to_user.message_id
            data['utc'] = event_info[0][8]
        await rem_bot.edit_message_reply_markup(chat_id=event_info[0][0], message_id=data['Первое сообщение'],
                                                reply_markup=None)  # Удаление инлайн кнопок из предыдущего сообщения
    else:
        await callback.message.answer('Что-то пошло не так\n Редактирование отменено')
        await callback.answer()
        await state.finish()

    await callback.answer()   # Ответ на коллбэк (ответ должен быть обязательно)
                              # Это убирает часики ожидания на кнопке

# Начало диалога для получения новых данных нового имени события
@disp.callback_query_handler(Text(startswith='click_edit'), state=FSM_edit_event.event_edit)
async def edit_current_event(callback : types.CallbackQuery, state:FSMContext):
    # Удаление инлайн кнопок из предыдущего сообщения
    async with state.proxy() as data:
        if data['Второе сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Второе сообщение'],
                                                reply_markup=None)
            data['Второе сообщение'] = False
    # Создание кнопки для нового имени
    inline_key = InlineKeyboardMarkup()                                   # Создание объекта клавиатуры
    old_name_button = InlineKeyboardButton(text='Оставить прежнее',
                                           callback_data='name_no_edit')  # Кнопка
    inline_key.add(old_name_button)
    mtu = await callback.message.answer('Введите новое имя события.', reply_markup=inline_key)
    # Получение id сообщения
    async with state.proxy() as data:
        data['Третье сообщение'] = mtu.message_id
    await FSM_edit_event.next()
    await callback.answer()

# Получение нового имени, сработает если нажата кнопка "Оставить прежнее"
@disp.callback_query_handler(Text(startswith='name_no_edit'), state=FSM_edit_event.event_new_name)
async def no_edit_name(callback:types.CallbackQuery, state:FSMContext):
    # Удаление инлайн кнопок из предыдущего сообщения
    async with state.proxy() as data:
        if data['Третье сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Третье сообщение'],
                                                reply_markup=None)
            data['Третье сообщение'] = False
    # Создание кнопки оставить для даты
    inline_key = InlineKeyboardMarkup()
    old_name_button = InlineKeyboardButton(text='Оставить прежнюю',
                                           callback_data='date_no_edit')  # Кнопка
    inline_key.add(old_name_button)
    await callback.message.answer(f'{eight_spoked_asterisk}Сохранено прежнее имя события')
    mtu = await callback.message.answer('Введите новую дату в формате: ДД.ММ.ГГГГ', reply_markup=inline_key)
    async with state.proxy() as data:
        data['Новое имя события'] = data['Имя события']
        data['Четвёртое сообщение'] = mtu.message_id
    await FSM_edit_event.next()
    await callback.answer()

# Получение нового имени, сработает если введено новое имя события
@disp.message_handler(state=FSM_edit_event.event_new_name)
async def edit_name(message : types.Message, state : FSMContext):
    # Удаление инлайн кнопок из предыдущего сообщения
    async with state.proxy() as data:
        if data['Третье сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Третье сообщение'],
                                                reply_markup=None)
            data['Третье сообщение'] = False
    # Создание кнопки оставить для даты
    inline_key = InlineKeyboardMarkup()  # Создание объекта клавиатуры
    old_date_button = InlineKeyboardButton(text='Оставить прежнюю',
                                           callback_data='date_no_edit')  # Кнопка
    inline_key.add(old_date_button)
    mtu = await rem_bot.send_message(message.chat.id, 'Введите новую дату в формате: ДД.ММ.ГГГГ',
                                     reply_markup=inline_key)
    async with state.proxy() as data:
        data['Новое имя события'] = message.text.lower()
        data['Четвёртое сообщение'] = mtu.message_id
    await FSM_edit_event.next()

# Получение новой даты, сработает если нажата кнопка "Оставить прежнюю"
@disp.callback_query_handler(Text(startswith='date_no_edit'), state=FSM_edit_event.event_new_date)
async def no_edit_date(callback:types.CallbackQuery, state:FSMContext):
    # Удаление инлайн кнопок из предыдущего сообщения
    async with state.proxy() as data:
        if data['Четвёртое сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Четвёртое сообщение'],
                                                reply_markup=None)
            data['Четвёртое сообщение'] = False
    await callback.message.answer(f'{eight_spoked_asterisk}Дата осталась неизменной.')
    # Создание кнопки оставить для времени
    inline_key = InlineKeyboardMarkup()  # Создание объекта клавиатуры
    old_time_button = InlineKeyboardButton(text='Оставить прежнее',
                                           callback_data='time_no_edit')  # Кнопка
    inline_key.add(old_time_button)

    mtu = await callback.message.answer('Введите новое время в формате: ЧЧ:ММ', reply_markup=inline_key)
    async with state.proxy() as data:
        data['Пятое сообщение'] = mtu.message_id
    await FSM_edit_event.event_new_time.set()
    await callback.answer()

# Получение новой даты, если введена новая
@disp.message_handler(state=FSM_edit_event.event_new_date)
async def edit_date(message:types.Message, state:FSMContext):
    # Удаление инлайн кнопок из предыдущего сообщения
    async with state.proxy() as data:
        # Проверка на отработку удаления кнопок
        if data['Четвёртое сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Четвёртое сообщение'],
                                                      reply_markup=None)
            data['Четвёртое сообщение'] = False
        new_date = check_date(message.text)  # Проверка корректности даты
        if new_date[0]:
            # Приведение даты к стандартному виду
            input_date = date_standrt(message.text)
            data['Дата'] = input_date
            # Переводим время в формат UTC
            zone = pytz.timezone(data['time_zone'])  # Создание объекта часового пояса
            user_loc_date = zone.localize(datetime.strptime(f"{data['Дата']} {data['Время']}", '%d.%m.%Y %H:%M'))
            loc_date = datetime.now(pytz.timezone(data['time_zone'])) \
                .replace(hour=0, minute=0, second=0, microsecond=0)  # Местная локальная дата
            # Проверка на прошлое
            if user_loc_date >= loc_date:
                # Создание кнопки оставить для времени
                inline_key = InlineKeyboardMarkup()
                old_time_button = InlineKeyboardButton(text='Оставить прежнее',
                                                   callback_data='time_no_edit')  # Кнопка
                inline_key.add(old_time_button)

                mtu = await rem_bot.send_message(message.chat.id, 'Введите время в формате: ЧЧ:ММ', reply_markup=inline_key)
                data['Пятое сообщение'] = mtu.message_id

                await FSM_edit_event.event_new_time.set()  # Переход к следующему состоянию машины
                await data.save()
            else:
                await message.reply('Дата прошла, введите другую')
        else:
            await message.reply(new_date[1])
            await rem_bot.send_message(message.chat.id, 'Введите дату снова.')

# Получение нового времени, сработает если нажата кнопка "Оставить прежнее"
@disp.callback_query_handler(Text(startswith='time_no_edit'), state=FSM_edit_event.event_new_time)
async def no_edit_time(callback:types.CallbackQuery, state:FSMContext):
    # Удаление инлайн кнопок из предыдущего сообщения
    async with state.proxy() as data:
        if data['Пятое сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Пятое сообщение'],
                                                reply_markup=None)
            data['Пятое сообщение'] = False
        await callback.message.answer(f'{eight_spoked_asterisk}Время осталось неизменным')
        await callback.answer()
        # Запись изменений в базу
        zone = pytz.timezone(data['time_zone'])  # Создание объекта часового пояса
        user_loc_date = zone.localize(datetime.strptime(f"{data['Дата']} {data['Время']}", '%d.%m.%Y %H:%M'))
        utc_time_to_base = user_loc_date.astimezone(pytz.utc).strftime('%d.%m.%Y %H:%M')  # Для записи а базу и перевод в UTC
        data['utc'] = utc_time_to_base
        if write_info(data, base=base, cursor=cursor):
            await callback.message.answer(f"{alarm_cloc}Событие успешно изменено\n"
                                      f"Событие: {data['Новое имя события']}\n"
                                      f"Дата: {data['Дата']}\n"
                                      f"Время: {data['Время']}")
            print('Замена произведена успешно')
            await state.finish()
        else:
            print('Ошибка при замене события')
            await state.finish()

# Получение нового времени если оно введено
@disp.message_handler(state=FSM_edit_event.event_new_time)
async def edit_time(message:types.Message, state:FSMContext):
    # Удаление инлайн кнопок из предыдущего сообщения
    async with state.proxy() as data:
        # Проверка на отработку удаления кнопок.
        if data['Пятое сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=data['id'], message_id=data['Пятое сообщение'],
                                                reply_markup=None)
            data['Пятое сообщение'] = False
        new_time = check_time(message.text)
        if new_time[0]:
            # Приведение времени к стандартному виду
            data['Время'] = time_standart(message.text)
            zone = pytz.timezone(data['time_zone'])  # Создание объекта часового пояса
            user_loc_time = zone.localize(datetime.strptime(f"{data['Дата']} {data['Время']}", '%d.%m.%Y %H:%M')) # Дата и время от пользователя
            local_time = datetime.now(zone).replace(second=0, microsecond=0)  # Получение текущего времени и даты
            utc_time_to_base = user_loc_time.astimezone(pytz.utc).strftime('%d.%m.%Y %H:%M')# Для записи а базу и перевод в UTC
            # Проверка времени на прошлое
            if user_loc_time > local_time:
                # Запись изменений в базу и проверка на успех.
                data['utc'] = utc_time_to_base
                if write_info(data, base=base, cursor=cursor):
                    await rem_bot.send_message(message.chat.id, f"{alarm_cloc}Событие успешно изменено\n"
                                              f"Событие: {data['Новое имя события']}\n"
                                              f"Дата: {data['Дата']}\n"
                                              f"Время: {data['Время']}")
                    print('Замена произведена успешно')
                    data.clear()
                    await state.finish()
                else:
                    print('Ошибка при замене события')
                    await rem_bot.send_message(message.chat.id, 'Что-то пошло не по плану, изменения не сохранены')
                    data.clear()
                    await state.finish()
            elif user_loc_time == local_time:
                await message.reply('Это прямо сейчас, не жди, действуй! =)')
                await state.finish()
            else:
                await message.reply('Время уже прошло, введите другое.')

        else:
            await message.reply(new_time[1])
            await rem_bot.send_message(message.chat.id, 'Введите время снова.')

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
    data_from_query = base_query(base=base, cursor=cursor, query=query, mode='search') # Поиск событий в базе
    # Проверка ответа базы и создание инлайновой клавиатуры.
    if data_from_query:
        button_mass = []
        async with state.proxy() as data:
            for line in data_from_query:
                id_button = line[7]          # Получение id события (записи)
                button_mass.append(InlineKeyboardButton(text=f'{line[5]}', callback_data=f'ueb{id_button}'))
                data[id_button] = line[5]    # Получение названия события

        # Создание клавиатуры
        inline_key = InlineKeyboardMarkup(row_width=2)  # Создание объекта клавиатуры, в ряд 2 кнопки
        inline_key.add(*button_mass)                    # добавление массива кнопок в объект клавиатуры
        inline_key.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))
        await message.answer('События в кнопках', reply_markup=inline_key)
    elif data_from_query is None:
        await rem_bot.send_message(message.chat.id, 'Ооп! Ошибочка с базой.')
        print('Ошибка с БД при удалении')
    else:
        await message.answer('Записей нет')
        await state.finish()

# Подтверждение удаления
@disp.callback_query_handler(Text(startswith='ueb'), state=FSM_delete_event.event_keyboard)
async def confirm_delete(callback:types.CallbackQuery, state:FSMContext):
    await FSM_delete_event.next()
    #await FSM_delete_event.event_delete.set()
    id_event = callback.data.replace('ueb', '')                # Вытягиваем локальный id события
    async with state.proxy() as data:
        event = data[id_event]
        data['Событие'] = event
        data['Удалить событие с id'] = id_event
    query = f"SELECT [date],[time] FROM 'event_from_users' WHERE [event] = '{event}' AND [id] = {callback.from_user.id}"
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
                   f"AND [id] = '{callback.from_user.id}' AND[id_event] = '{data['Удалить событие с id']}'"

    # Само удаление
    # Если запрос в базу отработал корректно
    if base_query(base=base, cursor=cursor, query=delete_query):
        # Запись в журнале
        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')  # Текущая дата и время
        first_name = callback.from_user.first_name                     # Получение имени пользователя
        user_id = callback.from_user.id                                # Получение id пользователя
        delete_log_query = f"INSERT INTO 'log' ([id], [first_name], [event], [action], [time])" \
                           f"VALUES ({user_id},'{first_name}','{data['Событие']}','delete', '{time_now}')"
        base_query(base=base, cursor=cursor, query=delete_log_query)   # Выполнение записи в журнал
        print(f"Событие: {data['Событие']} удалено, пользователь: {first_name}")
        await callback.message.answer(f"{cross_mark}Удалено событие: {data['Событие']}")
    else:
        await callback.message.answer('Ооп! Ошибочка! Удаление не сработало.')
        print('Ошибка удаления из базы')
    data.clear()               # Очистка словаря сданными после отработки удаления
    await callback.answer()
    await state.finish()

####################################### УДАЛЕНИЕ СОБЫТИЯ ##############################################################
# Стартовое сообщение
@disp.message_handler(commands=['start'])
async def welcome(message:types.Message):
    await rem_bot.send_message(message.chat.id, f'{public_address_loudspeaker} Привет! Это бот - напоминалка\n' +
                                            'Для взаимодействия используйте кнопки снизу\n' +
                                            'Вызов помощи "/help"\n' +
                                            'Настройки "/settings"')

    # Получение информации о пользователе запустившем бот.
    date = message.date.strftime('%d.%m.%Y %H:%M:%S')
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
        await rem_bot.send_message(message.chat.id, 'Часовой пояс по умолчанию: Беларусь UTC+03:00\n'
                                                    'Чтобы выбрать другой зайдите в настройки "/settings"')
        query_user_insert = f"INSERT INTO 'users' ([id],[first_name],[username],[date],[time_zone]) " \
                            f"VALUES ('{user_info['id']}','{user_info['Имя']}'," \
                            f"'{user_info['Имя пользователя']}','{user_info['Дата']}','Europe/Minsk');"
        if base_query(base=base, cursor=cursor, query=query_user_insert):
            print('Добавлен новый пользователь')
            print(user_info)
    user_info.clear()  # Очистка словаря с данными пользователя

    # Создание кнопок интерфейса бота
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)  # Создание объекта клавиатура
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
    await rem_bot.send_message(message.chat.id, f'{tangerine}Как с ним общаться:\n' +
                               '/start перезапуск\n' +
                               'Кнопка "Добавить событие" - добавить новое событие\n' +
                               'Кнопка "Показать мои события" - показывает все активные события пользователя запустившего бот\n' +
                               'Кнопка "Редактировать события" - открывает менюшку редактирования событий\n' +
                               'Кнопка "Удалить событие" - удаляет событие\n' +
                               'Для отмены нажать кнопку отмена, если такой нет, '
                               'то написать в сообщении: отмена\n' +
                               'Настроить часовой пояс: /settings')

# Настройки переписать через FSM  Сообщение с текущими настройками > выбор изменить или нет если да > кнопки с странами
# нет > сохранение выход и сообщение с текущими настройками

############################################### НАСТРОЙКИ ##############################################################
class FSM_settings(StatesGroup):
    first_message = State()
    choise_tz = State()
    save = State()

# Функция обработки команды /settings (Настройки)
@disp.message_handler(commands=['settings'], state=None)
async def settings(message:types.Message, state:FSMContext):
    tz_query = f"SELECT [time_zone] FROM 'users' WHERE [id] = {message.chat.id}"
    user_tz = base_query(base=base, cursor=cursor, query=tz_query, mode='search')[0][0]
    if user_tz is False:
        user_tz = 'Неуказанна'
    button_edit = InlineKeyboardButton(text='Редактировать', callback_data='click_edit')
    button_close = InlineKeyboardButton(text='Закрыть', callback_data='click_close')
    keyboard = InlineKeyboardMarkup().add(button_edit, button_close)
    mtu = await rem_bot.send_message(message.chat.id, f'Настройки\nЧасовой пояс: {user_tz}', reply_markup=keyboard)
    async with state.proxy() as sett:
        sett['Первое сообщение'] = mtu.message_id
        sett['id'] = message.from_user.id
    await FSM_settings.first_message.set()


# Функция обработки нажатия кнопки "Закрыть"
@disp.callback_query_handler(Text(startswith='click_close'), state=FSM_settings.first_message)
async def close_settings(callback:types.CallbackQuery, state:FSMContext):
    async with state.proxy() as sett:
        if sett['Первое сообщение']:
            await rem_bot.edit_message_reply_markup(chat_id=sett['id'], message_id=sett['Первое сообщение'],
                                                    reply_markup=None)
            sett['Первое сообщение'] = False
        sett.clear()
    await callback.message.answer('Настройки сохранены')
    await callback.answer()

    await state.finish()

@disp.callback_query_handler(Text(startswith='click_edit'), state=FSM_settings.first_message)
async def set_time_zone(callback:types.CallbackQuery, state:FSMContext):

    button_belerus = InlineKeyboardButton(text=f'{belarus}Беларусь UTC+03:00', callback_data='set_belarus')
    button_russia_moskau = InlineKeyboardButton(text=f'{russia}Россия(Москва) UTC+03:00', callback_data='set_russia_moskau')
    button_russia_vladivostok = InlineKeyboardButton(text=f'{russia}Россия(Владивосток) UTC+10:00', callback_data='set_russia_vladivostok')
    button_russia_kaliningrad = InlineKeyboardButton(text=f'{russia}Россия(Калининград) UTC+02:00', callback_data='set_russia_kaliningrad')
    button_ukraine = InlineKeyboardButton(text=f'{ukraine}Украина UTC+02:00', callback_data='set_ukraine')
    button_poland = InlineKeyboardButton(text=f'{poland}Польша UTC+01:00', callback_data='set_poland')
    button_czech_republic = InlineKeyboardButton(text=f'{czech}Чехия UTC+01:00', callback_data='set_czech')
    button_italy = InlineKeyboardButton(text=f'{italy}Италия UTC+01:00', callback_data='set_italy')
    button_litva = InlineKeyboardButton(text=f'{litva}Литва UTC+02:00', callback_data='set_litva')
    button_germany = InlineKeyboardButton(text=f'{germany}Германия UTC+01:00', callback_data='set_germany')
    button_antarctida = InlineKeyboardButton(text=f'{antarctida}Антарктида(Станция Восток) UTC+06:00', callback_data='set_antarctida')

    In_buttons = InlineKeyboardMarkup(row_width=2)
    In_buttons.add(button_belerus, button_russia_moskau, button_russia_vladivostok, button_russia_kaliningrad,
                   button_ukraine, button_poland, button_czech_republic, button_italy, button_litva, button_germany,
                   button_antarctida)

    await callback.message.answer('Выберите часовой пояс', reply_markup=In_buttons)
    await callback.answer()
    await FSM_settings.next()

@disp.callback_query_handler(Text(startswith='set'), state=FSM_settings.first_message)
async def set_user_time_zone(callback:types.CallbackQuery, state:FSMContext):
    # Дописать удаление кнопок после выбора
    time_zones = {'belarus' : 'Europe/Minsk',
                  'russia_moskau' : '',
                  'russia_vladivostok' : '',
                  'russia_kaliningrad' : '',
                  'ukraine' : '',
                  'poland' : 'Poland',
                  'set_czech' : '',
                  'set_italy' : '',
                  'litva' : '',
                  'germany' : '',
                  'antarctida' : ''
    }
    user_id = callback.from_user.id
    name_tz = callback.data.replace('set_', '')      # Вытягиваем название часового пояса
    current_tz = time_zones[name_tz]                 # Часовой пояс выбранный пользователем
    tz_query = f"UPDATE 'users' SET [time_zone] = '{current_tz}' WHERE [id] = {user_id}"
    if base_query(base=base, cursor=cursor, query=tz_query):
        pass
    else:
        pass
############################################### НАСТРОЙКИ ##############################################################

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
