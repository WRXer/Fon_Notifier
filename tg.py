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
ADMIN_ID = os.getenv('ADMIN_ID')

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

@bot.message_handler(commands=['help'])
async def help_handler(message):
    help_text = (
        "📌 **Список доступных команд**:\n\n"
        "/start - Запуск бота. После этой команды откроется главное меню.\n\n"
        "/help - Получить справочную информацию и описание команд.\n\n"
        "/donate - Поддержка проекта. Здесь можно отправить донат, если тебе нравится бот и его функциональность.\n\n"
        "Используй эти команды для взаимодействия с ботом и отслеживания событий!"
    )
    await bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['donate'])
async def donate_handler(message):
    donate_text = (
        "💰 **Поддержать проект можно следующими способами**:\n\n"
        "Через **CloudTips**: ▶️[На обслуживание бота 🔋](https://pay.cloudtips.ru/p/af008b92)◀️\n"
        "Спасибо за поддержку!"
    )
    await bot.send_message(message.chat.id, donate_text, parse_mode="Markdown")

@bot.message_handler(commands=['faq'])
async def help_handler(message):
    faq_text = (
        '📌 Чтобы начать пользоваться ботом нажимаем "start".\n'
        'После произойдет активация бота: \nвы будете внесены в список, кому слать уведомления.\n\n'
        'Для добавления лиги:\n'
        '- скинуть ссылку события из нужной вам лиги, либо просто лиги в формате https://fon.bet/live/hockey/11111/22222, \nгде 11111 - лига \n'
        '- /id номер лиги, например /id 11111\n\n'
        'Для удаления лиги:\n'
        '- /del номер лиги, например /del 11111 \n'
    )
    await bot.send_message(message.chat.id, faq_text, parse_mode="Markdown")

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

@bot.message_handler(commands=['admin'])
async def admin_handler(message):
    chat_id = message.chat.id
    if int(chat_id) == int(ADMIN_ID):    #Проверка, является ли пользователь администратором
        admin_text = ('Функции:\n'
                      '- /users Список пользователей\n'
                      '- /data Выгрузить базу данных\n'
                      )
        await bot.send_message(message.chat.id, admin_text, parse_mode="Markdown")
    else:
        await bot.send_message(chat_id, "У вас нет доступа к этой команде.")

@bot.message_handler(commands=['users'])
async def users_handler(message):
    chat_id = message.chat.id
    if int(chat_id) == int(ADMIN_ID):    #Проверка, является ли пользователь администратором
        league_data = load_data()
        users = list(league_data.keys())    #Получаем список всех пользователей
        if users:
            user_list = "\n".join([f"User ID: {user}" for user in users])
            await bot.send_message(chat_id, f"Список всех пользователей:\n{user_list}")
        else:
            await bot.send_message(chat_id, "Нет зарегистрированных пользователей.")
    else:
        await bot.send_message(chat_id, "У вас нет доступа к этой команде.")

@bot.message_handler(commands=['data'])
async def data_handler(message):
    chat_id = message.chat.id
    if int(chat_id) == int(ADMIN_ID):    #Проверка, является ли пользователь администратором
        if 'data.json':    #Проверяем, существует ли файл с данными
            with open('data.json', 'rb') as file:
                await bot.send_document(chat_id, file, caption="Вот файл с базой данных.")
        else:
            await bot.send_message(chat_id, "Файл данных не найден.")
    else:
        await bot.send_message(chat_id, "У вас нет доступа к этой команде.")

if __name__ == "__main__":
    asyncio.run(bot.infinity_polling(logger_level=True))
