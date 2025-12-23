
FROM n8nio/n8n:latest

USER root

RUN if command -v apk >/dev/null; then \
        apk add --no-cache python3 py3-pip ffmpeg; \
    elif command -v apt-get >/dev/null; then \
        apt-get update && apt-get install -y python3 python3-pip ffmpeg && rm -rf /var/lib/apt/lists/*; \
    elif command -v yum >/dev/null; then \
        yum install -y python3 python3-pip ffmpeg; \
    fi && \
    pip3 install --no-cache-dir yt-dlp

USER node
