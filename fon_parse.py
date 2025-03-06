import aiohttp

from work_data import load_data


sent_events = {}    #Словарь для отслеживания отправленных событий


async def fetch_and_display_events(user_chat_id):
    """
    Находим и выводим события, относящиеся к конкретному пользователю
    :param user_chat_id: chat_id пользователя
    :return:
    """
    data = load_data()
    if str(user_chat_id) not in data:    #Получаем sport_ids для конкретного пользователя
        return None    #Если пользователя нет в базе данных, возвращаем None
    user_sport_ids = set(data[str(user_chat_id)])
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://line52w.bk6bba-resources.com/events/list?lang=ru&version=36403772709&scopeMarket=1600'
        ) as response:
            data = await response.json()
    events = data.get('events', [])
    filtered_events = [
        event for event in events
        if event.get('place') == 'live' and
           event.get('sportId') in user_sport_ids and
           event.get('level') == 1
    ]    #Фильтруем нужные нам ивенты
    print(filtered_events)
    new_events = [
        event for event in filtered_events
        if event['id'] not in sent_events
    ]    #Добавляем новые ивенты в отправленные, чтобы не повторялась отправка
    print(new_events)
    if new_events:
        message_matches = ""
        for event in new_events:
            message_matches += (
                f"{event.get('team1')} - {event.get('team2')}\n"
            )
            sent_events[event['id']] = event    #Отмечаем событие как отправленное
        return message_matches
    else:
        return None
