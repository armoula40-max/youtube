from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid
import glob

app = Flask(__name__)

# ✅ Render paths (مش /app)
POSSIBLE_COOKIE_PATHS = [
    './cookies.txt',
    'cookies.txt', 
    '/opt/render/project/src/cookies.txt',
    '/app/cookies.txt'
]

COOKIES_PATH = next((p for p in POSSIBLE_COOKIE_PATHS if os.path.exists(p)), None)

@app.route('/')
def home():
    return jsonify({
        "status": "yt-dlp API ✅", 
        "cookies": "loaded ✅" if COOKIES_PATH else f"missing ({POSSIBLE_COOKIE_PATHS})",
        "cwd": os.getcwd(),
        "endpoints": ["/health", "/download"]
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "OK", 
        "cookies": COOKIES_PATH or "upload cookies.txt",
        "cwd": os.getcwd(),
        "cookie_paths_checked": len(POSSIBLE_COOKIE_PATHS)
    })

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    
    try:
        file_id = str(uuid.uuid4())[:8]
        output_path = f"/tmp/{file_id}.%(ext)s"
        
        ydl_opts = {
            'format': 'best[height<=720]',
            'noplaylist': True,
            'outtmpl': output_path,
            'cookies': COOKIES_PATH,  # ✅ Auto-detect
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'referer': 'https://www.youtube.com/',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        files = glob.glob(f"/tmp/{file_id}.*")
        if files:
            filename = os.path.basename(files[0])
            return jsonify({
                "status": "success",
                "file": filename,
                "download_url": f"https://youtube-fz9j.onrender.com/files/{filename}"
            })
        return jsonify({"error": "No file generated"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/<filename>')
def get_file(filename):
    return send_from_directory("/tmp", filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
