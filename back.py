import sqlite3
import re
import datetime

# Функция подключения к базе
# Функция выполняет подключение к базе, выполняет запрос query
# Если функция выполняет поиск, то возвращаются его результаты
# mode='search'
# Если запись или удаление, то True при успешной отработке

# Функция соединения с БД
def start_base():
    global base, cursor  # голобальные переменные с именем басы и курсором
    base = sqlite3.connect('users_data.db')
    cursor = base.cursor()
    if base:
        print('База успешно подключена')

def base_query(query='', mode=''):
    try:
        connection = sqlite3.connect('users_data.db')
        cursor = connection.cursor()
        cursor.execute(query)
        answer = cursor.fetchall()   # получение данных из запроса query
        cursor.close()
        connection.commit()
        connection.close()
        if mode == 'search':
            return answer
        else:
            return True
    except sqlite3.Error as erorr:
        print(f'Ошибка:{erorr}')
        return None

# Функция проверки корректности даты
def check_date(date):
    out_flag = False         # Выходной флаг функции
    correct_digit = False    # Флаг корректных чисел даты (месяц 01-12, день 01-31)
    # Словарь с количеством дней в месяцах
    date_now = datetime.datetime.now().strftime('%Y-%m-%d')  # Текущая дата
    #print(date_now)
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
def repeat_name():
    pass
