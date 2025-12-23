from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import uuid
import time
from pathlib import Path

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = Path("/app/downloads")
OUTPUT_DIR = Path("/app/output")
DOWNLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

def cleanup_old_files():
    current_time = time.time()
    for folder in [DOWNLOAD_DIR, OUTPUT_DIR]:
        for file in folder.glob("*"):
            if file.is_file() and (current_time - file.stat().st_mtime) > 1800:
                file.unlink()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "yt-dlp + ffmpeg API ✅",
        "endpoints": {"POST /download": "YouTube download + trim"}
    })

@app.route('/download', methods=['POST'])
def download_video():
    cleanup_old_files()
    
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url'"}), 400
        
        video_url = data['url']
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        file_name = data.get('file_name', str(uuid.uuid4()))
        
        download_path = DOWNLOAD_DIR / f"{uuid.uuid4()}.%(ext)s"
        output_path = OUTPUT_DIR / f"{file_name}.mp4"
        
        # yt-dlp download
        yt_dlp_cmd = [
            "yt-dlp", "-f", "best[height<=720]", 
            "-o", str(download_path), video_url
        ]
        result = subprocess.run(yt_dlp_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500
        
        # Find downloaded file
        downloaded_file = list(DOWNLOAD_DIR.glob("*.mp4"))[0]
        
        if start_time and end_time:
            duration = end_time - start_time
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-ss", str(start_time), 
                "-i", str(downloaded_file), "-t", str(duration),
                "-c", "copy", str(output_path)
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True, timeout=120)
            downloaded_file.unlink()
        else:
            downloaded_file.rename(output_path)
        
        download_url = f"{request.url_root.rstrip('/')}/files/{output_path.name}"
        
        return jsonify({
            "status": "success",
            "video_url": download_url,
            "file_name": output_path.name
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
