FROM python:3.9-slim

RUN apt-get update && apt-get install -y ffmpeg git gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir openai-whisper pillow flask numpy Werkzeug

COPY . .

EXPOSE 10000

CMD ["python", "main.py", "--server", "--host", "0.0.0.0", "--port", "10000"]
