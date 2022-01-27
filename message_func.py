import asyncio

# Фоновая функция
async def cickle_func():
    print('Запуск фоновой функции')
    while True:
        print('Фоновая функция работает')
        await asyncio.sleep(20)