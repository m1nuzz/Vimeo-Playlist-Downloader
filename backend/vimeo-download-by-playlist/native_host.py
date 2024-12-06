#!/usr/bin/env python

import sys
import json
import struct
import subprocess
import os
import logging
from datetime import datetime

# Настраиваем логирование
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'native_host.log')
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_message(message):
    """Отправляем сообщение в Chrome"""
    try:
        message_json = json.dumps(message)
        message_bytes = message_json.encode('utf-8')
        sys.stdout.buffer.write(struct.pack('I', len(message_bytes)))
        sys.stdout.buffer.write(message_bytes)
        sys.stdout.buffer.flush()
        logging.debug(f"Sent message: {message}")
    except Exception as e:
        logging.error(f"Error sending message: {str(e)}")

def read_message():
    """Читаем сообщение из Chrome"""
    try:
        text_length_bytes = sys.stdin.buffer.read(4)
        if len(text_length_bytes) == 0:
            logging.warning("Input stream closed")
            return None

        text_length = struct.unpack('I', text_length_bytes)[0]
        text = sys.stdin.buffer.read(text_length).decode('utf-8')
        logging.debug(f"Received message: {text}")
        return json.loads(text)
    except Exception as e:
        logging.error(f"Error reading message: {str(e)}")
        return None

def handle_download(data):
    """Обрабатываем команду на скачивание"""
    try:
        path = data.get('path')
        urls = data.get('urls', [])
        
        if not path or not urls:
            logging.error("Invalid download request: missing path or urls")
            return False

        # Создаем полный путь для сохранения
        download_path = os.path.abspath(path)
        os.makedirs(download_path, exist_ok=True)

        # Запускаем скрипт скачивания для каждого URL
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vimeo-dl-by-playlist.py')
        
        for url in urls:
            try:
                cmd = [
                    'python',
                    script_path,
                    '--url', url,
                    '--output', download_path
                ]
                
                logging.debug(f"Running command: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logging.error(f"Download failed for {url}: {result.stderr}")
                else:
                    logging.info(f"Successfully downloaded {url}")
                    
            except Exception as e:
                logging.error(f"Error downloading {url}: {str(e)}")
                continue

        return True
    except Exception as e:
        logging.error(f"Error in handle_download: {str(e)}")
        return False

def handle_ping():
    """Обрабатываем пинг для проверки доступности"""
    return True

def main():
    """Основной цикл обработки сообщений"""
    logging.info("Native host started")
    
    while True:
        try:
            message = read_message()
            if message is None:
                logging.warning("No message received, exiting")
                break

            action = message.get('action')
            if not action:
                logging.error("No action specified in message")
                send_message({"success": False, "error": "No action specified"})
                continue

            if action == 'ping':
                success = handle_ping()
                send_message({"success": success})
            
            elif action == 'download':
                success = handle_download(message)
                send_message({"success": success})
            
            else:
                logging.warning(f"Unknown action: {action}")
                send_message({"success": False, "error": f"Unknown action: {action}"})

        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            send_message({"success": False, "error": str(e)})
            break

    logging.info("Native host stopped")

if __name__ == '__main__':
    main()
