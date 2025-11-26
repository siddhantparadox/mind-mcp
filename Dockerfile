FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GRADIO_SERVER_NAME=0.0.0.0

WORKDIR /app

# System deps for downloading sqlite-vec
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates unzip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install sqlite-vec: prefer local build at ./sqlite-vec/vec0.so if present,
# otherwise try the upstream install script.
RUN set -eux; \
    if [ -f /app/sqlite-vec/vec0.so ]; then \
        cp /app/sqlite-vec/vec0.so /usr/local/lib/vec0.so; \
    else \
        curl -L 'https://github.com/asg017/sqlite-vec/releases/latest/download/install.sh' -o /tmp/install.sh; \
        sh /tmp/install.sh; \
        if [ -f /usr/local/lib/vec0.so ]; then \
            :; \
        elif [ -f /app/vec0.so ]; then \
            cp /app/vec0.so /usr/local/lib/vec0.so; \
        elif [ -f /usr/local/lib/sqlite-vec/vec0.so ]; then \
            cp /usr/local/lib/sqlite-vec/vec0.so /usr/local/lib/vec0.so; \
        else \
            echo "sqlite-vec was not installed; add sqlite-vec/vec0.so to the repo or adjust SQLITE_VEC_PATH" && exit 1; \
        fi; \
    fi

# Ensure data directory exists for volume binding
RUN mkdir -p /app/data

EXPOSE 7860

CMD ["python", "-m", "mind.main"]
