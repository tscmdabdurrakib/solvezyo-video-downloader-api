FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y ffmpeg \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
