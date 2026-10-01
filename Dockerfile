FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install exact locked dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

EXPOSE 8000

# --proxy-headers allows uvicorn to trust the X-Forwarded-* headers set by the
# nginx reverse proxy so request.client shows the real client IP.
# The app is not exposed to the host anymore, so nginx is the only trusted peer.
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]