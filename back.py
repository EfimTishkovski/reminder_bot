import sqlite3
import re
import datetime


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
    out_flag = False         # Выходной флаг функции
    correct_digit = False    # Флаг корректных чисел даты (месяц 01-12, день 01-31)
    # Словарь с количеством дней в месяцах
    date_now = datetime.datetime.now().strftime('%Y-%m-%d')  # Текущая дата
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

    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', date) is not None:

        date_mass = map(int, date.split('-'))
        date_mass = list(date_mass)
        date_mass_now = map(int, date_now.split('-'))
        date_mass_now = list(date_mass_now)

        # Проверка на корректные числа
        if 1 <= date_mass[1] <= 12 and 1 <= date_mass[2] <= 31:
            # Проверка на корректность дней в месяце (чтобы не было 31 сентября и подобного)
            if date_mass[2] <= day_in_month[date_mass[1]]:
                correct_digit = True
                # Дописать обработку високосного года и февраля

        # Проверка на "более раннюю" дату
        if correct_digit:
            # Сравниваем год
            if date_mass[0] > date_mass_now[0]:
                out_flag = True
            elif date_mass[0] == date_mass_now[0]:
                # Сравниваем месяц
                if date_mass[1] > date_mass_now[1]:
                    out_flag = True
                elif date_mass[1] == date_mass_now[1]:
                    # Сравниваем день
                    if date_mass[2] >= date_mass_now[2]:
                        out_flag = True
                    else:
                        return False, 'Эта дата уже прошла'
                else:
                    return False, 'Эта дата уже прошла'
            else:
                return False, 'Эта дата уже прошла'
        if out_flag:
            return True, 'Дата корректна'
        else:
            return False,'Дата не корректна'
    else:
        return False, 'Формат даты не корректен'

# Функция проверки корректности времени
def check_time(time):
    pass

# Функция проверки имени события в базе (повторяющиеся имена)
# True - норм, не повторяется
# False - имя уже занято
# Дописать проверку по id у разных пользователей могут быть события с одинаковыми именами.
def repeat_name(name_event, base, cursor):
    query = f"SELECT * FROM 'event_from_users' WHERE [event] = '{name_event}'"
    if base_query(base=base, cursor=cursor, query=query, mode='search'):
        return False  # Имя уже занято
    else:
        return True   # Имя свободно совпадений нет
