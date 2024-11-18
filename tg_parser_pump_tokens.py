import time
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from loguru import logger

# Ваши API_ID и API_HASH, которые вы можете получить, зарегистрировавшись на my.telegram.org
api_id = ''
api_hash = ''
phone = ''  # Номер телефона, который используется для регистрации в Telegram

# Имя вашего сессийного файла, который будет создан
session_name = 'session_name'

# Ссылка на телеграм-канал
channel_username = 'https://t.me/bananadeployerSOL'
output_file = 'call_analyser_pump.txt'
calls_file = 'calls_pump.txt'

# Список имён пользователей получателей сообщений
destination_usernames = ['aaaa349'] 

keywords = ["Caller Stats"]  # Ключевые слова
target_length = 44  # Длина эталонного значения

logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")

def extract_text_between_markers(text, start_marker, end_marker):
    start_idx = text.find(start_marker)
    if start_idx != -1:
        start_idx += len(start_marker)
        end_idx = text.find(end_marker, start_idx)
        if end_idx != -1:
            return text[start_idx:end_idx].strip()
    return ""

def contains_keywords(text, keywords):
    for keyword in keywords:
        if keyword in text:
            return True
    return True

def find_word_by_length_and_suffix(text, target_length, suffix):
    words = text.split()
    for word in words:
        if len(word) in {target_length, target_length-1, target_length+1} and word.endswith(suffix):
            return word
    return None

with TelegramClient(session_name, api_id, api_hash) as client:
    # Получаем информацию о канале
    channel = client.get_entity(channel_username)
    destinations = [client.get_entity(username) for username in destination_usernames]
    last_message_id = 0

    while True:
        try:
            # Получаем историю сообщений канала
            history = client(GetHistoryRequest(
                peer=channel,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=200,  # Количество сообщений для получения за один запрос
                max_id=0,
                min_id=last_message_id,
                hash=0
            ))

            # Проверяем, есть ли новые сообщения
            if history.messages:
                with open(output_file, 'a', encoding='utf-8-sig') as f_all, open(calls_file, 'a', encoding='utf-8-sig') as f_calls:
                    for message in history.messages:
                        if message.id > last_message_id:
                            # Записываем все сообщения в call_analyser.txt
                            f_all.write(f"{message.date} - {message.sender_id} - {message.message}\n")
                            logger.info(f"Message logged: {message.date} - {message.sender_id} - {message.message}")

                            if message.message:
                                if contains_keywords(message.message, keywords):
                                    # Извлекаем текст между ")" и "🍌 Type"
                                    extracted_text = extract_text_between_markers(message.message, ")", "🍌 Type")
                                    logger.info(f"Extracted text: {extracted_text}")

                                    # Находим слово нужной длины и проверяем окончание
                                    found_word = find_word_by_length_and_suffix(extracted_text, target_length, 'pump')
                                    if found_word:
                                        logger.info(f"Valid word found: {found_word}")
                                        # Записываем в calls.txt
                                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        for destination in destinations:
                                            client.send_message(destination, found_word)
                                            logger.info(f"Message sent to {destination.username}: {found_word}")
                                        f_calls.write(f"{message.date} - {current_time} - {message.sender_id} - {found_word}\n")
                                        logger.info(f"Valid call logged: {message.date} - {current_time} - {message.sender_id} - {found_word}")

                            last_message_id = message.id
            else:
                logger.warning("No new messages found.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

        # Ожидаем 2 секунды перед следующим запросом
        time.sleep(2)
