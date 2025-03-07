import asyncio
import telebot
import logging
import os, re
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
        tasks = []    #Список задач для отправки сообщений
        for chat_id in chat_ids:
            message_matches = await loop.run_in_executor(None, fetch_and_display_events, chat_id)

            if message_matches:
                tasks.append(bot.send_message(chat_id, text=message_matches))    #Добавляем задачу в список
            else:
                logging.info(f"Для {chat_id} нет новых событий.")    #Логируем, если нет событий
        if tasks:
            await asyncio.gather(*tasks)    #Запускаем отправку сообщений параллельно
    except Exception as e:
        logging.error(f"Ошибка в send_message: {e}")
    asyncio.create_task(schedule_next_message())

async def schedule_next_message():
    await asyncio.sleep(60)    #Ждем 60 секунд перед отправкой следующего сообщения
    await send_message()    #Отправляем сообщение и снова планируем следующую задачу

@bot.message_handler(commands=['start'])
async def start_handler(message):
    chat_id = message.chat.id
    chat_ids.add(chat_id)    #Добавляем chat_id в список
    await bot.send_message(chat_id, "Бот активирован")
    await send_message()    #Запускаем отправку сообщения

@bot.message_handler(commands=['id'])
async def id_handler(message):
    """
    Возможность добавления id пользователями
    :param message:
    :return:
    """
    chat_id = message.chat.id
    try:
        league_id = int(message.text.split()[1])
        data = load_data()

        if str(chat_id) not in data:
            data[str(chat_id)] = []

        if league_id in data[str(chat_id)]:
            await bot.send_message(chat_id, f"ID {league_id} уже существует в списке.")
        else:
            data[str(chat_id)].append(league_id)
            save_data(data)
            await bot.send_message(chat_id, f"ID {league_id} добавлен в список.")
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
        league_id = int(message.text.split()[1])
        data = load_data()

        if str(chat_id) in data and league_id in data[str(chat_id)]:
            data[str(chat_id)].remove(league_id)
            save_data(data)
            await bot.send_message(chat_id, f"ID {league_id} удален из списка.")
        else:
            await bot.send_message(chat_id, f"ID {league_id} не найден в списке.")
    except (IndexError, ValueError):
        await bot.send_message(chat_id, "Пожалуйста, введите правильный ID для удаления, используя формат /del <число>.")

@bot.message_handler(func=lambda message: message.text.startswith("https://"))
async def handle_link(message):
    """
    Обрабатывает, если кидают ссылку
    :param message:
    :return:
    """
    chat_id = str(message.chat.id)
    fon_link = re.search(r'https://fon\.bet/.*?(\d+)(?:/|$)', message.text)
    if not fon_link:    #Если не нашли ID, то ничего не делаем
        return
    league_id = int(fon_link.group(1))    #Возвращаем найденное число
    data = load_data()
    if chat_id not in data:     #Добавляем sport_id пользователю, если его ещё нет
        data[chat_id] = []
    if league_id not in data[chat_id]:
        data[chat_id].append(league_id)
        save_data(data)
        await bot.send_message(chat_id, f"ID лиги {league_id} добавлен в ваш список.")
    else:
        await bot.send_message(chat_id, f"ID лиги {league_id} уже есть в вашем списке.")


if __name__ == "__main__":
    asyncio.run(bot.infinity_polling(logger_level=True))
