import requests

from work_data import load_data


sent_events = {}    #Словарь для отслеживания отправленных событий


def fetch_and_display_events(chat_id):
    """
    Получает события только для конкретного chat_id.
    """
    global sent_events    #Используем глобальный словарь
    if chat_id not in sent_events:
        sent_events[chat_id] = set()    #У каждого пользователя свой список отправленного
    data = load_data()
    user_league_ids = data.get(str(chat_id), [])
    if not user_league_ids:
        return None

    s = requests.Session()
    s.headers = {
        'Accept': 'application/json',
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    response = s.get('https://line52w.bk6bba-resources.com/events/list?lang=ru&version=36403772709&scopeMarket=1600')
    data = response.json()

    events = data.get('events', [])
    filtered_events = [
        event for event in events
        if event.get('place') == 'live' and
           event.get('sportId') in user_league_ids and
           event.get('level') == 1
    ]
    new_events = [event for event in filtered_events if event['id'] not in sent_events[chat_id]]
    if new_events:
        message_matches = "\n".join(f"{event.get('team1')} - {event.get('team2')}" for event in new_events)
        sent_events[chat_id].update(
            event['id'] for event in new_events)    #Запоминаем отправленные только для этого юзера
        return message_matches
    return None
