FROM python:3.9-slim
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV CELERY_BROKER_URL=amqp://guest:guest@rabbit:5672//
ENV CELERY_RESULT_BACKEND=mongodb://mongodb:27017/celery_backend

EXPOSE 8000

CMD celery -A tasks worker --loglevel=info & uvicorn app:app --host 0.0.0.0 --port 8000
