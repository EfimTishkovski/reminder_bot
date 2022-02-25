import sqlite3
import re
import datetime
import random
from string import ascii_lowercase

# Функция соединения с БД возвращает объект типа sqlite3 (база и курсор)
def start_base():
    #global base, cursor  # глобальные переменные с именем базы и курсором
    base = sqlite3.connect('users_data.db')
    cursor = base.cursor()
    if base:
        print('База успешно подключена')
        return base, cursor
    else:
        print('Ошибка подключения к базе')

# Функция выполняет подключение к базе, выполняет запрос query
# Если функция выполняет поиск, то возвращаются его результаты
# mode='search'
# Если запись или удаление, то True при успешной отработке
def base_query(base, cursor, query='', mode=''):
    try:
        cursor.execute(query)
        base.commit()
        if mode == 'search':
            answer = cursor.fetchall()  # получение данных из запроса query
            return answer
        else:
            return True
    except sqlite3.Error as erorr:
        print(f'Ошибка:{erorr}')
        return None

# Функция закрытия соединения с базой
def stop_base(base, cursor):
    base.commit()
    cursor.close()
    base.close()
    print('Соединение с базой закрыто')

# Функция проверки корректности даты
def check_date(date):
    # Словарь с количеством дней в месяцах
    day_in_month = {1 : 31,
                    2 : 28,
                    3 : 31,
                    4 : 30,
                    5 : 31,
                    6 : 30,
                    7 : 31,
                    8 : 31,
                    9 : 30,
                    10 : 31,
                    11 : 30,
                    12 : 31}

    if re.fullmatch(r'\d{1,2}\.\d{1,2}\.\d{4,6}', date) is not None:
        date_mass = map(int, str(date).split('.'))
        date_mass = list(date_mass)
        # Проверка на корректные числа
        if 1 <= date_mass[1] <= 12 and 1 <= date_mass[0] <= 31:
            # Проверка на корректность дней в месяце (чтобы не было 31 сентября и подобного)
            if date_mass[0] <= day_in_month[date_mass[1]]:
                return True, 'Дата корректна'
            else:
                return False, 'Дата не корректна'
                # Дописать обработку високосного года и февраля
        else:
            return False, 'Дата не корректна'
    else:
        return False, 'Формат даты не корректен'

# Функция проверки корректности времени
# date - дата от пользователя, проверяется предыдущей функцией имеет формат ДД.ММ.ГГГГ
def check_time(time):
    # Входной шаблон
    if re.fullmatch(r'\d{1,2}:\d{1,2}', time) is not None:
        time_mass = map(int, str(time).split(':'))
        time_mass = list(time_mass)
        # Проверка на корректные числа
        if 0 <= time_mass[0] <= 23 and 0 <= time_mass[1] <= 59:
            return True, ''
        else:
            return False, f'Числа не корректны, часы от 0 до 23, минуты от 0 до 59.'

    else:
        return False, 'Формат времени не корректен, введите время в формате ЧЧ:ММ.'

# Функция проверки имени события в базе (повторяющиеся имена)
# True - норм, не повторяется
# False - имя уже занято
"""
def repeat_name(name_event, id, base, cursor):
    query = f"SELECT * FROM 'event_from_users' WHERE [event] = '{name_event}' AND [id] = {id}"
    if base_query(base=base, cursor=cursor, query=query, mode='search'):
        return False  # Имя уже занято
    else:
        return True   # Имя свободно совпадений нет
"""
# Функция генерации id события
def generate_id():
    out = '@' + str(random.randint(1001, 9999)) + random.choice(ascii_lowercase) + '@' + str(random.randint(0, 999))
    return out

# Функция завершения диалога и записи в базу (для редактирования)
def write_info(data, base, cursor):
    try:
        replace_query = f"UPDATE 'event_from_users' SET [date] = '{data['Дата']}'," \
                    f"[time] = '{data['Время']}'," \
                    f"[event] = '{data['Новое имя события']}'," \
                    f"[status] = '{'wait'}'," \
                    f"[UTC] = '{data['utc']}' " \
                    f"WHERE [id] = {data['id']} AND [event] = '{data['Имя события']}';"
        if base_query(base=base, cursor=cursor, query=replace_query) is None:
            return False
        # Запись в журнал
        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')  # Текущая дата и время
        name_query = f"SELECT first_name FROM 'users' WHERE [id] = {data['id']}"
        user_name = base_query(base=base, cursor=cursor, query=name_query, mode='search')
        if data['Имя события'].lower() != data['Новое имя события'].lower():
            change_name = '>' + data['Новое имя события']  # меняем имя
        else:
            change_name = ''  # Имя неизменно
        log_query = f"INSERT INTO 'log' ([id], [first_name], [event], [action], [time])" \
                f"VALUES ({data['id']}, '{user_name[0][0]}'," \
                f"'{data['Имя события']} {change_name}', 'edit', '{time_now}')"
        base_query(base=base, cursor=cursor, query=log_query)  # Отметка в журнале
        return True
    except sqlite3.Error as erorr:
        print(erorr)
        return False

# Функция приведения даты к стандартному формату
def date_standrt(date):
    date_mass = date.split('.')
    if int(date_mass[1]) < 10 and len(date_mass[1]) < 2:
        date_mass[1] = f"0{date_mass[1]}"
    if int(date_mass[2]) < 10 and len(date_mass[2]) < 2:
        date_mass[2] = f"0{date_mass[2]}"
    return f"{date_mass[0]}.{date_mass[1]}.{date_mass[2]}"

# Функция приведения времени к стандарту
def time_standart(time):
    time_mass = time.split(':')
    if int(time_mass[0]) < 10 and len(time_mass[0]) < 2:
        time_mass[0] = f"0{time_mass[0]}"
    if int(time_mass[1]) < 10 and len(time_mass[1]) < 2:
        time_mass[1] = f"0{time_mass[1]}"
    return f"{time_mass[0]}:{time_mass[1]}"

# Функция получения часового пояса пользователя из базы
def get_time_zone(us_id, base, cursor):
    query = f"SELECT UTC FROM 'users' WHERE [id] = {us_id} "
    answer = base_query(base=base, cursor=cursor, query=query, mode='search')
    return answer[0][0]
"""
# Функция проверки даты, прошла или нет формат UTC ?
def past_date(date):
    date_now = datetime.datetime.utcnow()
    user_date = datetime.datetime.strptime(date, '%d.%m.%Y %H:%M')
    if date_now > user_date:
        return False
    else:
        return True
"""