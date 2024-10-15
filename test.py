import asyncio, telebot
import logging
import os
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv

from setup_logging import setup_logging
from test2 import fetch_and_display_events


load_dotenv()

TOKEN_BOT = os.getenv('TOKEN_BOT')
LOG_LEVEL = True

setup_logging()  # Вызываем функцию для настройки логирования

bot = AsyncTeleBot(TOKEN_BOT)
telebot.logger.setLevel(LOG_LEVEL)


chat_ids = set()    # Глобальный список для хранения chat_id пользователей


async def send_message():
    try:
        loop = asyncio.get_running_loop()
        message_matches = await loop.run_in_executor(None, fetch_and_display_events)     # Выполняем синхронную функцию в асинхронном контексте
        if message_matches:    # Проверяем, есть ли что отправить
            for chat_id in chat_ids:
                await bot.send_message(chat_id, text=message_matches)
    except Exception as e:
        logging.error(f"An error occurred in send_message: {e}")
    asyncio.create_task(schedule_next_message())    # Планируем выполнение задачи через 10 секунд без использования цикла


async def schedule_next_message():
    await asyncio.sleep(60)    # Ждем 10 секунд перед отправкой следующего сообщения
    await send_message()    # Отправляем сообщение и снова планируем следующую задачу


@bot.message_handler(commands=['start'])
async def start_handler(message):
    chat_id = message.chat.id
    chat_ids.add(chat_id)    # Добавляем chat_id в список
    await bot.send_message(chat_id, "Start")
    await send_message()    # Запускаем отправку сообщения


@bot.message_handler(commands=['id'])
async def id_handler(message):
    """
    Добавил возможность добавления id пользователям
    :param message:
    :return:
    """
    chat_id = message.chat.id
    try:
        sport_id = int(message.text.split()[1])
        with open('sport_ids.txt', 'r') as f:    # Чтение существующих ID из файла
            existing_ids = {int(line.strip()) for line in f if line.strip().isdigit()}

        if sport_id in existing_ids:
            await bot.send_message(chat_id, f"ID {sport_id} уже существует в списке.")
        else:
            with open('sport_ids.txt', 'a') as f:
                f.write(f"{sport_id}\n")
            await bot.send_message(chat_id, f"ID {sport_id} добавлен в список.")
    except (IndexError, ValueError):
        await bot.send_message(chat_id, "Пожалуйста, введите правильный ID, используя формат /id <число>.")


if __name__ == "__main__":
    asyncio.run(bot.infinity_polling(logger_level=True))
