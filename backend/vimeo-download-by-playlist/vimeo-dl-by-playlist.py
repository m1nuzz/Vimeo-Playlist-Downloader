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
import time

# Создаем логгер
logger = setup_logger('downloader')

def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов Windows"""
    # Список недопустимых символов Windows
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    filename = ''.join(char if char not in invalid_chars else '_' for char in filename)
    
    # Заменяем множественные пробелы одним
    filename = ' '.join(filename.split())
    
    # Обрезаем длину имени файла
    if len(filename) > 100:  
        filename = filename[:97] + "..."
    
    # Убираем пробелы в начале и конце
    filename = filename.strip()
    
    # Если имя пустое после очистки, используем значение по умолчанию
    if not filename:
        filename = "video"
        
    return filename

def extract_title_from_html(html_content):
    # Implement your HTML title extraction logic here
    pass

def download_video(url, output_path, video_title=None, html_content=None):
    try:
        if not video_title and html_content:
            video_title = extract_title_from_html(html_content)
        
        if not video_title:
            video_title = "video"
            
        # Очищаем имя файла в самом начале
        original_title = video_title
        video_title = sanitize_filename(video_title)
        if original_title != video_title:
            logger.info(f"Original title '{original_title}' was sanitized to '{video_title}'")
            
        # Создаем основную директорию для видео
        video_dir = os.path.join(output_path, video_title)
        try:
            os.makedirs(video_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory '{video_dir}': {str(e)}")
            raise

        logger.info(f'Starting download for URL: {url}')
        logger.info(f'Output path: {video_dir}')

        # Создаем временную директорию
        temp_dir = os.path.join(video_dir, 'temp')
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create temp directory '{temp_dir}': {str(e)}")
            raise

        logger.info(f'Created temp directory: {temp_dir}')

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
        output_filename = f"{video_title}_{best_video['video_res']}.mp4"
        output_file = os.path.join(video_dir, output_filename)
        logger.info(f"Merging video and audio to: {output_file}")
        
        try:
            # Add a small delay before FFmpeg operation
            time.sleep(1)
            
            # First verify input files exist and are not empty
            if not (os.path.exists(video_output) and os.path.exists(audio_output)):
                raise Exception("Input video or audio file missing")
                
            if os.path.getsize(video_output) == 0 or os.path.getsize(audio_output) == 0:
                raise Exception("Input video or audio file is empty")
            
            # Run FFmpeg with more detailed error output
            result = subprocess.run([
                'ffmpeg',
                '-i', video_output,
                '-i', audio_output,
                '-c', 'copy',
                output_file
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")
                
            # Verify output file was created and is not empty
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                raise Exception("Output file was not created or is empty")
                
        except Exception as e:
            logger.error(f"Error during video merge: {str(e)}")
            if os.path.exists(output_file):
                os.remove(output_file)
            raise

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
