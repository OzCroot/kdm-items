FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Data volume mount point
VOLUME /data

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "scraper.py"]
