FROM python:3.11-slim

# تثبيت الأدوات
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# تثبيت yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp && \
    chmod +x /usr/local/bin/yt-dlp

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# الكود
COPY . .

# المجلدات
RUN mkdir -p /tmp /app/downloads /app/output && chmod 755 /tmp

EXPOSE $PORT

CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--timeout", "600", "api:app"]
