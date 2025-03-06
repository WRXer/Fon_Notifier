import asyncio
import telebot
import logging
import os
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv

from setup_logging import setup_logging
from fon_parse import fetch_and_display_events
from work_data import load_data, save_data

load_dotenv()

TOKEN_BOT = os.getenv('TOKEN_BOT')
LOG_LEVEL = True

setup_logging()    #Вызываем функцию для настройки логирования

bot = AsyncTeleBot(TOKEN_BOT)
telebot.logger.setLevel(LOG_LEVEL)


chat_ids = set()    #Глобальный список для хранения chat_id пользователей


async def send_message():
    try:
        loop = asyncio.get_running_loop()
        message_matches = await loop.run_in_executor(None, fetch_and_display_events)    #Выполняем синхронную функцию в асинхронном контексте
        if message_matches:    #Проверяем, есть ли что отправить
            for chat_id in chat_ids:
                await bot.send_message(chat_id, text=message_matches)
    except Exception as e:
        logging.error(f"An error occurred in send_message: {e}")
    asyncio.create_task(schedule_next_message())    #Планируем выполнение задачи через 10 секунд без использования цикла

async def schedule_next_message():
    await asyncio.sleep(60)    #Ждем 10 секунд перед отправкой следующего сообщения
    await send_message()    #Отправляем сообщение и снова планируем следующую задачу

@bot.message_handler(commands=['start'])
async def start_handler(message):
    chat_id = message.chat.id
    chat_ids.add(chat_id)  # Добавляем chat_id в список
    await bot.send_message(chat_id, "Start")
    message_matches = await fetch_and_display_events(chat_id)    #Получаем события для конкретного пользователя
    if message_matches:
        await bot.send_message(chat_id, message_matches)    #Отправляем события только этому пользователю
    else:
        await bot.send_message(chat_id, "У вас нет лиг для просмотра событий.")

@bot.message_handler(commands=['id'])
async def id_handler(message):
    """
    Возможность добавления id пользователями
    :param message:
    :return:
    """
    chat_id = message.chat.id
    try:
        sport_id = int(message.text.split()[1])
        data = load_data()

        if str(chat_id) not in data:
            data[str(chat_id)] = []

        if sport_id in data[str(chat_id)]:
            await bot.send_message(chat_id, f"ID {sport_id} уже существует в списке.")
        else:
            data[str(chat_id)].append(sport_id)
            save_data(data)
            await bot.send_message(chat_id, f"ID {sport_id} добавлен в список.")
    except (IndexError, ValueError):
        await bot.send_message(chat_id, "Пожалуйста, введите правильный ID, используя формат /id <число>.")

@bot.message_handler(commands=['del'])
async def del_handler(message):
    """
    Возможность удаления del пользователями
    :param message:
    :return:
    """
    chat_id = message.chat.id
    try:
        sport_id = int(message.text.split()[1])
        data = load_data()

        if str(chat_id) in data and sport_id in data[str(chat_id)]:
            data[str(chat_id)].remove(sport_id)
            save_data(data)
            await bot.send_message(chat_id, f"ID {sport_id} удален из списка.")
        else:
            await bot.send_message(chat_id, f"ID {sport_id} не найден в списке.")
    except (IndexError, ValueError):
        await bot.send_message(chat_id, "Пожалуйста, введите правильный ID для удаления, используя формат /del <число>.")


if __name__ == "__main__":
    asyncio.run(bot.infinity_polling(logger_level=True))
