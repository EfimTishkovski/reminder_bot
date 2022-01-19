import sqlite3
import re
import datetime

# Функция подключения к базе
# Функция выполняет подключение к базе, выполняет запрос query
# Если функция выполняет поиск, то возвращаются его результаты
# mode='search'
# Если запись или удаление, то True при успешной отработке
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
    flag = False
    # Словарь с количеством дней в месяцах
    date_now = datetime.datetime.now().strftime('%Y-%m-%d')  # Текущая дата
    print(date_now)
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
        #print('ok')
        # Проверка на "более раннюю" дату
        date_mass = map(int, date.split('-'))
        date_mass = list(date_mass)
        date_mass_now = map(int, date_now.split('-'))
        date_mass_now = list(date_mass_now)
        #Сравниваем год
        if date_mass[0] > date_mass_now[0]:
            flag = True
        elif date_mass[0] == date_mass_now[0]:
            # Сравниваем месяц
            if date_mass[1] > date_mass[1]:
                flag = True
            elif date_mass[1] == date_mass[1]:
                # Сравниваем день
                if date_mass[2] >= date_mass[2]:
                    flag = True
        if flag:
            print('ok')
        else:
            print('noy')

    else:
        print('no')
