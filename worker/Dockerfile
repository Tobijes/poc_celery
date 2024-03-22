FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models /app/models

COPY tasks.py .

CMD ["celery", "--app", "tasks", "worker", "--pool=solo", "--loglevel=info"]
