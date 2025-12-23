

FROM n8nio/n8n:latest

USER root

RUN apt-get update -qq && \
    apt-get install -y python3 python3-pip ffmpeg && \
    pip3 install yt-dlp && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER node
