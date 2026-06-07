FROM node:22-alpine AS css
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY tailwind.config.js ./
COPY static/src ./static/src
RUN npm run build:css

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=css /app/static/css/styles.css ./static/css/styles.css

RUN python manage.py collectstatic --noinput --settings=ministry_manager.settings.production 2>/dev/null || true

EXPOSE 8000
CMD ["gunicorn", "ministry_manager.wsgi:application", "--bind", "0.0.0.0:8000"]
