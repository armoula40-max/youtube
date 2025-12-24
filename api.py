from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid
import glob
import subprocess

app = Flask(__name__)

# ✅ مسارات الكوكيز المحتملة في Render
POSSIBLE_COOKIE_PATHS = [
    './cookies.txt',
    'cookies.txt', 
    '/opt/render/project/src/cookies.txt',
    '/app/cookies.txt',
    '/tmp/cookies.txt'
]

COOKIES_PATH = next((p for p in POSSIBLE_COOKIE_PATHS if os.path.exists(p)), None)

@app.route('/')
def home():
    return jsonify({
        "status": "yt-dlp API ✅", 
        "cookies": "✅ موجود" if COOKIES_PATH else "❌ مفقود - ارفع cookies.txt",
        "cookies_from_browser": "مدعوم",
        "cwd": os.getcwd(),
        "endpoints": ["/health", "/download (POST)"],
        "example": '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "cookies_browser": "chrome"}'
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "OK", 
        "cookies_file": COOKIES_PATH or "لا يوجد",
        "cookies_from_browser": "مدعوم",
        "yt_dlp_version": subprocess.getoutput("yt-dlp --version") if subprocess.run(["yt-dlp", "--version"], capture_output=True).returncode == 0 else "غير مثبت"
    })

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "❌ يجب إرسال URL"}), 400
    
    try:
        file_id = str(uuid.uuid4())[:8]
        output_path = f"/tmp/{file_id}.%(ext)s"
        
        # ✅ دعم cookies_from_browser + cookies_file
        ydl_opts = {
            'format': 'best[height<=720]',
            'noplaylist': True,
            'outtmpl': output_path,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
        }
        
        # 1️⃣ Cookies من المتصفح (الأولوية الأولى)
        cookies_browser = data.get('cookies_browser') or data.get('cookies_from_browser')
        if cookies_browser:
            ydl_opts['cookiesfrombrowser'] = cookies_browser
            print(f"✅ استخدام cookies من {cookies_browser}")
        
        # 2️⃣ ملف كوكيز (backup)
        elif COOKIES_PATH:
            ydl_opts['cookies'] = COOKIES_PATH
            print(f"✅ استخدام cookies من {COOKIES_PATH}")
        else:
            print("⚠️ لا توجد كوكيز - قد يفشل مع بعض الفيديوهات")
        
        # 3️⃣ إعدادات إضافية لتجنب bot detection
        ydl_opts.update({
            'extractor_retries': 3,
            'fragment_retries': 3,
            'sleep_interval': 1,
            'max_sleep_interval': 5,
        })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print(f"✅ تم تحميل: {info.get('title', 'Unknown')}")
        
        # البحث عن الملف
        files = glob.glob(f"/tmp/{file_id}.*")
        if files:
            filename = os.path.basename(files[0])
            return jsonify({
                "status": "✅ نجح",
                "title": info.get('title', 'غير معروف'),
                "file": filename,
                "download_url": f"https://youtube-fz9j.onrender.com/files/{filename}",
                "cookies_used": cookies_browser or COOKIES_PATH or "لا شيء"
            })
        
        return jsonify({"error": "❌ لم يتم إنشاء ملف"}), 500
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ خطأ: {error_msg}")
        return jsonify({
            "error": error_msg,
            "solution": "جرب cookies_browser: 'chrome' أو ارفع cookies.txt"
        }), 500

@app.route('/files/<filename>')
def get_file(filename):
    if os.path.exists(f"/tmp/{filename}"):
        return send_from_directory("/tmp", filename, as_attachment=True, max_age=3600)
    return jsonify({"error": "❌ الملف غير موجود"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
