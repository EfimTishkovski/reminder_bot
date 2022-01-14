import sqlite3

# Функция подключения к базе
# Функция выполняет подключение к базе, выполняет запрос query
# Если функция выполняет поиск, то возвращаются его результаты
# mode='search'
# Если запись или удаление, то True при успешной отработке
def base_query(query=''):
    try:
        connection = sqlite3.connect('users_data.db')
        cursor = connection.cursor()
        cursor.execute(query)
        answer = cursor.fetchall()   # получение данных из запроса query
        cursor.close()
        connection.commit()
        connection.close()

        return answer
    except sqlite3.Error as erorr:
        print(f'Ошибка:{erorr}')
        return None