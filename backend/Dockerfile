FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
WORKDIR /app/foodgram
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]