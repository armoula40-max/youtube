from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import os
import uuid
import time
import shutil
from pathlib import Path

app = Flask(__name__)
CORS(app)

# المسارات
DOWNLOAD_DIR = Path("/app/downloads")
OUTPUT_DIR = Path("/app/output")
DOWNLOAD_DIR.mkdir(exist_ok=True, mode=0o755)
OUTPUT_DIR.mkdir(exist_ok=True, mode=0o755)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "yt-dlp API ✅",
        "endpoints": ["/health", "/download (POST)"],
        "example": '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "OK", "yt-dlp": "ready"})

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "Missing URL"}), 400
        
        # إنشاء اسم ملف فريد
        file_id = str(uuid.uuid4())[:8]
        temp_file = f"/tmp/{file_id}.%(ext)s"
        output_file = f"/tmp/{file_id}_output.mp4"
        
        # yt-dlp تحميل
        cmd = [
            "yt-dlp", "-f", "best[height<=720]", 
            "--no-playlist", "-o", temp_file, url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return jsonify({"error": "Download failed", "log": result.stderr}), 500
        
        # البحث عن الملف المحمل
        temp_path = Path("/tmp").glob(f"{file_id}.*")
        downloaded = next(temp_path, None)
        
        if not downloaded:
            return jsonify({"error": "No file downloaded"}), 500
        
        # نسخ للإخراج
        shutil.copy2(downloaded, output_file)
        
        return jsonify({
            "status": "success",
            "file": f"{file_id}_output.mp4",
            "download_url": f"{request.host_url.rstrip('/')}/files/{Path(output_file).name}"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/<filename>')
def get_file(filename):
    return send_from_directory("/tmp", filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)
