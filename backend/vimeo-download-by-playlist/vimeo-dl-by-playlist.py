#!/usr/bin/env python
import subprocess
import requests
import shutil
import os
import re
import json
import sys
import traceback
import argparse
from logger_config import setup_logger

# Создаем логгер
logger = setup_logger('downloader')

def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов и обрезает длинные имена"""
    # Заменяем недопустимые символы на underscore
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # Удаляем точки в конце имени файла (Windows не позволяет)
    filename = filename.rstrip('.')
    
    # Ограничиваем длину имени файла (Windows MAX_PATH = 260)
    max_length = 200  # Оставляем место для расширения и пути
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    return filename.strip()

def download_video(url, output_path, video_title=None, html_content=None):
    """Скачивает видео по URL"""
    try:
        logger.info(f'Starting download for URL: {url}')
        logger.info(f'Output path: {output_path}')

        # Создаем директорию для видео (без дополнительной вложенной папки)
        video_title = sanitize_filename(video_title) if video_title else 'untitled_video'
        video_dir = output_path  # Используем напрямую переданный путь
        os.makedirs(video_dir, exist_ok=True)
        logger.info(f'Using video directory: {video_dir}')

        # Создаем временную директорию
        temp_dir = os.path.join(video_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Проверяем наличие необходимых инструментов
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("yt-dlp is not installed")
            return False

        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg is not installed")
            return False

        # Получаем playlist.json
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        }

        try:
            bef_v2 = re.findall(r'(https:.*exp.*hmac.*)/v2/playlist', url)[0].strip()
        except IndexError:
            logger.error('This is not a v2 playlist.json link!')
            return False

        logger.debug(f'Base URL: {bef_v2}')
        
        resp = requests.get(url, headers=headers).json()
        logger.debug(f'Playlist response: {json.dumps(resp, indent=2)}')

        # Получаем видео и аудио потоки
        video_streams = resp.get('video', [])
        audio_streams = resp.get('audio', [])

        if not video_streams:
            logger.error("No video streams found in response!")
            return False

        # Подготавливаем данные о потоках
        video_data = [
            {
                'id': re.match(r'(.*?)-', video['id']).group(1),
                'width': video.get('width', 0),
                'height': video.get('height', 0),
                'video_res': f"{video.get('width', 0)}x{video.get('height', 0)}",
                'video_link': f"{bef_v2}/parcel/video/{re.match(r'(.*?)-', video['id']).group(1)}.mp4"
            }
            for video in video_streams
        ]

        audio_data = [
            {
                'id': re.match(r'(.*?)-', audio['id']).group(1),
                'codecs': audio.get('codecs', 'unknown'),
                'bitrate': audio.get('bitrate', 0),
                'audio_details': f"{audio.get('codecs', 'unknown')}, {audio.get('bitrate', 0)}",
                'audio_link': f"{bef_v2}/parcel/audio/{re.match(r'(.*?)-', audio['id']).group(1)}.mp4"
            }
            for audio in audio_streams
        ]

        # Сортируем потоки по качеству
        video_data.sort(key=lambda x: (x['width'], x['height']), reverse=True)
        audio_data.sort(key=lambda x: x['bitrate'], reverse=True)

        # Берем лучшее качество
        best_video = video_data[0]
        best_audio = audio_data[0]

        logger.info(f"Selected video quality: {best_video['video_res']}")
        logger.info(f"Selected audio quality: {best_audio['audio_details']}")

        # Скачиваем видео
        video_output = os.path.join(temp_dir, 'video.mp4')
        logger.info(f"Downloading video to: {video_output}")
        subprocess.run([
            'yt-dlp', '-N', '16', '--no-warning', '--no-check-certificate',
            '-o', video_output, best_video['video_link']
        ], check=True)

        # Скачиваем аудио
        audio_output = os.path.join(temp_dir, 'audio.aac')
        logger.info(f"Downloading audio to: {audio_output}")
        subprocess.run([
            'yt-dlp', '-N', '16', '--no-warning', '--no-check-certificate',
            '-o', audio_output, best_audio['audio_link']
        ], check=True)

        # Объединяем видео и аудио
        output_file = os.path.join(video_dir, f"{video_title}_{best_video['video_res']}.mp4")
        logger.info(f"Merging video and audio to: {output_file}")
        subprocess.run([
            'ffmpeg', '-v', 'quiet', '-stats', '-y',
            '-i', video_output,
            '-i', audio_output,
            '-c', 'copy', output_file
        ], check=True)

        # Очищаем временные файлы
        logger.info("Cleaning up temporary files")
        shutil.rmtree(temp_dir)

        logger.info("Download completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description='Download Vimeo videos')
    parser.add_argument('--url', required=True, help='URL of the video to download')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--title', help='Video title')
    parser.add_argument('--html', help='HTML content of the page')
    
    try:
        args = parser.parse_args()
        
        # Проверяем и создаем директорию
        if not os.path.exists(args.output):
            logger.info(f'Creating output directory: {args.output}')
            os.makedirs(args.output)
        
        # Скачиваем видео
        success = download_video(args.url, args.output, args.title, args.html)
        
        if not success:
            logger.error('Download failed')
            sys.exit(1)
            
    except Exception as e:
        logger.error(f'Error in main: {str(e)}')
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
