import asyncio
import datetime
import back

# Фоновая функция отслеживания событий
async def remin_func():
    now_time = datetime.datetime.now().strftime('%H-%M-%S')  # Текущее время
    now_date = datetime.datetime.now().strftime('%Y-%m-%d')  # Текущая дата
    now_time_mass = list(map(int, now_time.split('-')))
    print(now_time[:-3])
    print(now_date)
    second = (60 - int(now_time_mass[2])) + 1
    print(second)
    # Запуск в 01 секунду любой минуты
    while True:
        await asyncio.sleep(1)
        break
    print('Запуск фоновой функции')
    while True:
        print('Фоновая функция работает')
        await asyncio.sleep(10)
        global base, cursor
        query = f"SELECT event FROM 'event_from_users' WHERE [date] = '{now_date}' AND [time] = '{now_time}'"
        event_mass = back.base_query(base=base, cursor=cursor, query=query, mode='search')
        print(event_mass)
