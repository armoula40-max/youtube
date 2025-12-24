from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid
import glob

app = Flask(__name__)

# ✅ Cookies path في Render
COOKIES_PATH = "/app/cookies.txt" if os.path.exists("/app/cookies.txt") else None

@app.route('/')
def home():
    return jsonify({
        "status": "yt-dlp API ✅", 
        "cookies": "loaded" if COOKIES_PATH else "missing",
        "endpoints": ["/health", "/download"]
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "OK", 
        "cookies": "available" if COOKIES_PATH else "upload cookies.txt",
        "cwd": os.getcwd()
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
        
        # ✅ Anti-bot options
        ydl_opts = {
            'format': 'best[height<=720]',
            'noplaylist': True,
            'outtmpl': output_path,
            'cookies': COOKIES_PATH,  # ✅ Cookies
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',  # ✅ Real browser
            'referer': 'https://www.youtube.com/',  # ✅ Referer
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
    try:
        return send_from_directory("/tmp", filename, as_attachment=True)
    except:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
