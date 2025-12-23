FROM python:3.11-slim

# تثبيت ffmpeg + yt-dlp
RUN apt-get update && apt-get install -y ffmpeg curl && apt-get clean

# تثبيت yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
RUN chmod +x /usr/local/bin/yt-dlp

WORKDIR /app

# نسخ requirements أولاً
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "600", "api:app"]