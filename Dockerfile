FROM python:3.14-slim-bookworm

# Prevent Python from writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /artwork-uploader

# Copy only requirements first for better layer caching
COPY requirements.txt .

# Install dependencies (homelab fork: no unpinned pip self-upgrade on every build)
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Hardened (homelab fork): run as an unprivileged user. The code stays root-owned and read-only
# to the app; only the runtime-state folders are writable. APP_UID/APP_GID should match the
# owner of the host folders mounted at config/ and bulk_imports/.
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g "${APP_GID}" app \
 && useradd -r -m -u "${APP_UID}" -g app -s /usr/sbin/nologin app \
 && mkdir -p config logs bulk_imports downloads uploads \
 && chown app:app config logs bulk_imports downloads uploads
USER app

# Expose web UI port
EXPOSE 4567

# Declare volume for bulk imports
VOLUME ["/artwork-uploader/bulk_imports"]

# Health check configuration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; exit(0 if urllib.request.urlopen('http://localhost:4567/api/health').getcode() == 200 else 1)"

# Run application
ENTRYPOINT ["python", "artwork_uploader.py"]
