import asyncio
import datetime
# Фоновая функция
async def reminer_func():
    now_time = datetime.datetime.now().strftime('%H-%M-%S')  # Текущее время
    now_time_mass = now_time.split('-')
    # Запуск не позднее 58 секунды, чтобы функция успевала отработать и не ошибалась минутой
    while True:
        if int(now_time_mass[2]) < 58:
            break
        else:
            await asyncio.sleep(3)
            break
    print('Запуск фоновой функции')
    while True:
        print('Фоновая функция работает')
        await asyncio.sleep(20)