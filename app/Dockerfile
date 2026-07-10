FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN mkdir -p logs

# Set dummy env vars ONLY for this build step
# They do NOT persist in the final image
# ECS will inject real values at runtime
RUN SECRET_KEY=build-dummy-key-not-used-in-production \
    DB_NAME=postgres \
    DB_USER=postgres \
    DB_PASSWORD=postgres \
    DB_HOST=localhost \
    DB_PORT=5432 \
    EMAIL_HOST=smtp.gmail.com \
    EMAIL_PORT=587 \
    EMAIL_USE_TLS=True \
    EMAIL_HOST_USER=dummy@example.com \
    EMAIL_HOST_PASSWORD=dummy \
    DEFAULT_FROM_EMAIL=dummy@example.com \
    CORS_ALLOWED_ORIGINS=http://localhost \
    JWT_ACCESS_TOKEN_LIFETIME=60 \
    JWT_REFRESH_TOKEN_LIFETIME=7 \
    MAX_LOGIN_ATTEMPTS=5 \
    LOGIN_LOCKOUT_DURATION=30 \
    python manage.py collectstatic --noinput

# Production: gunicorn with stdout logging for CloudWatch
CMD ["gunicorn", "core.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output"]


# old....
#FROM python:3.11-slim

# ENV PYTHONUNBUFFERED=1 \
#     PYTHONDONTWRITEBYTECODE=1 \
#     PIP_NO_CACHE_DIR=1 \
#     PIP_DISABLE_PIP_VERSION_CHECK=1

# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     postgresql-client \
#     build-essential \
#     libpq-dev \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Install Python dependencies
# COPY requirements.txt .
# RUN pip install --upgrade pip && \
#     pip install -r requirements.txt

# # Copy project
# COPY . .

# # Create logs directory
# RUN mkdir -p logs

# # Collect static files — fail build if this breaks
# RUN python manage.py collectstatic --noinput

# # Production: gunicorn with stdout logging for CloudWatch
# CMD ["gunicorn", "core.wsgi:application", \
#      "--bind", "0.0.0.0:8000", \
#      "--workers", "4", \
#      "--timeout", "120", \
#      "--access-logfile", "-", \
#      "--error-logfile", "-", \
#      "--capture-output"]
