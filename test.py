import locale
import asyncio, telebot
import os
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv
from test2 import fetch_and_display_events


load_dotenv()

TOKEN_BOT = os.getenv('TOKEN_BOT')
LOG_LEVEL = True

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')  # Установка локали на русский язык

bot = AsyncTeleBot(TOKEN_BOT)
telebot.logger.setLevel(LOG_LEVEL)

# Глобальный список для хранения chat_id пользователей
chat_ids = set()
group_chat_id = -4527112396

async def send_message():
    loop = asyncio.get_running_loop()
    # Выполняем синхронную функцию в асинхронном контексте
    message_matches = await loop.run_in_executor(None, fetch_and_display_events)
    if message_matches:  # Проверяем, есть ли что отправить
        for chat_id in chat_ids:
            await bot.send_message(chat_id, text=message_matches)
        await bot.send_message(group_chat_id, text=message_matches)

    # Планируем выполнение задачи через 10 секунд без использования цикла
    asyncio.create_task(schedule_next_message())


async def schedule_next_message():
    await asyncio.sleep(10)  # Ждем 10 секунд перед отправкой следующего сообщения
    await send_message()  # Отправляем сообщение и снова планируем следующую задачу


async def start_sending_messages():
    await send_message()


@bot.message_handler(commands=['start'])
async def start_handler(message):
    chat_id = message.chat.id
    chat_ids.add(chat_id)  # Добавляем chat_id в список
    await bot.send_message(chat_id, "Start")
    await send_message()  # Запускаем отправку сообщения


if __name__ == "__main__":
    asyncio.run(send_message())
    asyncio.run(bot.infinity_polling(logger_level=True))
