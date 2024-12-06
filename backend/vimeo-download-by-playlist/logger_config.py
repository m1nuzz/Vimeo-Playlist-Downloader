import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name, log_file='download_system.log', level=logging.INFO):
    """Настройка логгера с ротацией файлов"""
    
    # Очищаем старый лог файл
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except Exception as e:
            print(f"Не удалось очистить лог файл: {e}")
    
    # Создаем форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Создаем обработчик для файла с ротацией
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.ERROR)  # Записываем в файл только ошибки
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # В консоль пишем информационные сообщения
    
    # Настраиваем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Удаляем старые обработчики если они есть
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Создаем общий логгер для всей системы
system_logger = setup_logger('system')
