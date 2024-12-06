from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import traceback
from datetime import datetime
from logger_config import setup_logger

app = Flask(__name__)
CORS(app)

# Создаем логгер для сервера
logger = setup_logger('server')

@app.route('/ping', methods=['GET'])
def ping():
    logger.info('Received ping request')
    return jsonify({'status': 'ok'})

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.json
        if not data or 'videos' not in data:
            error_msg = 'No video data received'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        videos = data['videos']
        if not videos:
            error_msg = 'Empty video list'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400

        # Создаем базовую директорию для загрузок с временной меткой
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_dir = os.path.join('Downloads', f'vimeo_download_{timestamp}')
        os.makedirs(base_dir, exist_ok=True)

        # Сохраняем список ссылок
        with open(os.path.join(base_dir, 'playlist_links.txt'), 'w', encoding='utf-8') as f:
            for video in videos:
                f.write(f"{video['url']}\n")

        # Обрабатываем каждое видео
        for video in videos:
            try:
                video_title = video['title'].strip()
                if not video_title:
                    video_title = 'untitled_video'
                
                # Создаем директорию для видео (без дополнительной вложенной папки)
                video_dir = os.path.join(base_dir, video_title)
                os.makedirs(video_dir, exist_ok=True)

                # Сохраняем страницу в формате HTML
                html_path = os.path.join(video_dir, f"{video_title}.html")
                
                # Сохраняем HTML контент
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(video['html'])

                # Запускаем скрипт загрузки
                script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vimeo-dl-by-playlist.py')
                cmd = [
                    'python',
                    script_path,
                    '--url', video['url'],
                    '--output', video_dir,
                    '--title', video_title
                ]

                logger.info(f"Starting download for {video_title}")
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    logger.error(f"Download failed for {video_title}")
                    logger.error(f"Error output: {result.stderr}")
                else:
                    logger.info(f"Successfully started download for {video_title}")

            except Exception as e:
                logger.error(f"Error processing video {video.get('title', 'unknown')}: {str(e)}")
                logger.error(traceback.format_exc())
                continue

        return jsonify({
            'status': 'success',
            'message': f'Started download of {len(videos)} videos',
            'save_path': base_dir
        })

    except Exception as e:
        error_msg = f"Error in download endpoint: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/save_page', methods=['POST'])
def save_page():
    try:
        data = request.get_json()
        html_content = data.get('html')
        file_path = data.get('path')
        
        if not html_content or not file_path:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save HTML content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return jsonify({'success': True, 'message': 'Page saved successfully'})
        
    except Exception as e:
        logger.error(f"Failed to save page: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Создаем директорию Downloads если её нет
    downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    logger.info('Starting server on http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
