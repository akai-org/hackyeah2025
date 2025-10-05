FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "hackyeah2025_backend.asgi:application"]
