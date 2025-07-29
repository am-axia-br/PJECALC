# =============================
# Dockerfile
# =============================
FROM python:3.11

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt