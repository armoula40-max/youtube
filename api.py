from flask import Flask, request, jsonify, send_from_directory
import subprocess
import os
import uuid
import glob
import time

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "yt-dlp API ✅",
        "endpoints": ["/health", "/download (POST)"],
        "example": '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
    })

@app.route('/health')
def health():
    return jsonify({"status": "OK", "timestamp": time.time()})

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "Missing URL"}), 400
        
        file_id = str(uuid.uuid4())[:8]
        output_pattern = f"/tmp/{file_id}.%(ext)s"
        
        # yt-dlp
        cmd = ["yt-dlp", "-f", "best[height<=720]", "--no-playlist", "-o", output_pattern, url]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/app", timeout=300)
        
        if result.returncode != 0:
            return jsonify({"error": "Download failed", "log": result.stderr[:500]}), 500
        
        # البحث عن الملف
        files = glob.glob(f"/tmp/{file_id}.*")
        if not files:
            return jsonify({"error": "No file found"}), 500
        
        filename = os.path.basename(files[0])
        return jsonify({
            "status": "success",
            "file": filename,
            "download_url": f"{request.host}/files/{filename}"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/<filename>')
def get_file(filename):
    return send_from_directory("/tmp", filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
