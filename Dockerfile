FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ws_server.py .

CMD ["python", "ws_server.py"]