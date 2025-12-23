from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid
import glob
import time

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "yt-dlp API ✅", 
        "endpoints": ["/health", "/download (POST)"]
    })

@app.route('/health')
def health():
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            version = ydl._ies['GenericIE']._call_api('version')
        return jsonify({"status": "OK", "yt-dlp": f"v{version}", "cwd": os.getcwd()})
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)[:100]}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({"error": "Missing URL"}), 400
        
        file_id = str(uuid.uuid4())[:8]
        output_path = f"/tmp/{file_id}.%(ext)s"
        
        ydl_opts = {
            'format': 'best[height<=720]',
            'noplaylist': True,
            'outtmpl': output_path,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # ابحث عن الملف المُولد
        files = glob.glob(f"/tmp/{file_id}.*")
        if not files:
            return jsonify({"error": "No file generated"}), 500
        
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
    try:
        return send_from_directory("/tmp", filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
