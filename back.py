import sqlite3

# Функция подключения к базе
# Функция выполняет подключение к базе, выполняет запрос query
# И обрабатывает результат функцией function
def base_query(function, query=''):
    try:
        connection = sqlite3.connect('users_data.db')
        cursor = connection.cursor()
        cursor.execute(query)
        answer = cursor.fetchall()   # получение данных из запроса query
        rez = function(answer)       # Обработка данных на входе функции массив
        cursor.close()
        connection.close()
        return rez
    except sqlite3.Error as erorr:
        print(f'Ошибка:{erorr}')
        return False