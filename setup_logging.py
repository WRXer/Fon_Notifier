import logging


def setup_logging(log_file='bot_log.txt', log_level=logging.DEBUG):
    """
    Настраивает логирование.

    :param log_file: Путь к файлу для сохранения логов.
    :param log_level: Уровень логирования.
    """
    logging.basicConfig(
        filename=log_file,
        filemode='a',    # Режим 'a' означает, что лог будет дописываться в конец файла
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log_level
    )
    logging.info("Logging is set up.")
