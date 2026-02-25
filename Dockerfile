FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# App Runner typically routes to PORT (often 8080). Expose 8080 for clarity.
EXPOSE 8080

# Use gunicorn for production, bind to $PORT
CMD ["sh", "-c", "gunicorn -w 2 -k gthread -t 120 -b 0.0.0.0:${PORT:-8080} app:app"]