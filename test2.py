import requests


sent_events = {}  # Словарь для отслеживания отправленных событий

def fetch_and_display_events():
    """
    Находим и выводим события
    :return:
    """
    with open('sport_ids.txt', 'r') as f:
        sport_ids = [int(line.strip()) for line in f if line.strip().isdigit()]

    s = requests.Session()
    s.headers = {
        'Accept': 'application/json',
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    response = s.get(
        'https://line52w.bk6bba-resources.com/events/list?lang=ru&version=36403772709&scopeMarket=1600'
    )
    data = response.json()


    #sport_ids = [113000, 49280, 17428, 24713]  # Укажите ID лиги, которую хотите отфильтровать

    events = data.get('events', [])
    filtered_events = [
        event for event in events
        if event.get('place') == 'live' and
           event.get('sportId') in sport_ids and
           event.get('level') == 1
    ]

    new_events = [
        event for event in filtered_events
        if event['id'] not in sent_events
    ]

    if new_events:
        message_matches = ""
        for event in new_events:
            message_matches += (
                f"Матч {event.get('team1')} - {event.get('team2')} начинается!\n"
            )
            sent_events[event['id']] = event  # Отмечаем событие как отправленное

        return message_matches
    else:
        return None
