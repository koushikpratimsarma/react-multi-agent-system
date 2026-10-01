# Docker Setup Guide

This project includes Docker configuration for easy deployment and local development.

## Quick Start

### Prerequisites

* Docker Desktop installed on your system
* Docker Compose available through Docker Desktop

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your actual API keys and PostgreSQL credentials:

```env
TAVILY_API_KEY=your_tavily_api_key
OPENAI_API_KEY=your_openai_api_key
EXA_API_KEY=your_exa_api_key

POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=agents
```

> Never commit `.env` to GitHub. It contains secrets.

### 2. Run with Docker Compose

Start the PostgreSQL database, FastAPI application, and nginx reverse proxy:

```bash
docker compose up -d
```

Docker Compose will:

1. Start the PostgreSQL container.
2. Create the `agents` database.
3. Wait until PostgreSQL is healthy.
4. Start the FastAPI application.
5. Start the nginx reverse proxy in front of the FastAPI application.
6. Connect FastAPI to PostgreSQL through the Docker network.

The application is now served **through the nginx reverse proxy**, which is the single public entry point:

```text
http://localhost:8080
```

The port is controlled by `NGINX_PORT` in `.env` (default `8080`). If you change it to e.g. `80`, the app is served at `http://localhost`.

> The FastAPI container is **not** exposed on the host anymore. Only the nginx container publishes a port, and it forwards everything to `app:8000` over the internal Docker network.

The FastAPI Swagger documentation is still available through the proxy:

```text
http://localhost:8080/docs
```

Check the health endpoint through nginx:

```bash
curl http://localhost:8080/health
```

### 3. View Logs

View FastAPI application logs:

```bash
docker compose logs -f app
```

View PostgreSQL logs:

```bash
docker compose logs -f postgres
```

View logs for all services:

```bash
docker compose logs -f
```

### 4. Check Running Services

```bash
docker compose ps
```

The PostgreSQL service should eventually show:

```text
healthy
```

### 5. Stop Services

Stop the containers:

```bash
docker compose down
```

To also remove the PostgreSQL database volume:

```bash
docker compose down -v
```

> `docker compose down -v` deletes the PostgreSQL data stored in the Docker volume. Use it carefully.

## Building the Docker Image Manually

If you want to build the FastAPI Docker image without Docker Compose:

```bash
docker build -t agents:latest .
```

You can check the image with:

```bash
docker images
```

However, for this project, Docker Compose is recommended because the application also requires PostgreSQL.

## Environment Variables

The project requires the following environment variables:

| Variable            | Purpose                  |
| ------------------- | ------------------------ |
| `TAVILY_API_KEY`    | Tavily search API key    |
| `OPENAI_API_KEY`    | OpenAI API key           |
| `EXA_API_KEY`       | Exa search API key       |
| `POSTGRES_USER`     | PostgreSQL username      |
| `POSTGRES_PASSWORD` | PostgreSQL password      |
| `POSTGRES_DB`       | PostgreSQL database name |
| `NGINX_PORT`        | Host port for the nginx reverse proxy (default `8080`) |

Docker Compose uses these variables to create the PostgreSQL connection string for the FastAPI application.

Inside Docker, the application uses:

```text
postgresql://POSTGRES_USER:POSTGRES_PASSWORD@postgres:5432/POSTGRES_DB
```

The hostname is `postgres` because `postgres` is the PostgreSQL service name in `docker-compose.yml`.

> Do not use `localhost` for the PostgreSQL hostname inside the FastAPI container. `localhost` would refer to the FastAPI container itself.

## File Descriptions

* **Dockerfile** - Defines the Docker image for the FastAPI application.
* **docker-compose.yml** - Runs and connects the PostgreSQL, FastAPI, and nginx services.
* **nginx/default.conf** - Nginx reverse-proxy config: routes all traffic to the FastAPI app and keeps Server-Sent Events un-buffered.
* **.dockerignore** - Excludes unnecessary files from the Docker build context.
* **.env.example** - Template showing the required environment variables.
* **.env** - Contains the actual API keys and database credentials. This file should not be committed to GitHub.
* **uv.lock** - Locks the Python dependency versions used by the project.
* **pyproject.toml** - Defines the Python project and its dependencies.

## Troubleshooting

### Container fails to start

Check the application logs:

```bash
docker compose logs app
```

You can also check all containers:

```bash
docker compose ps
```

### Database connection error

Check PostgreSQL:

```bash
docker compose ps
```

The `postgres` service should show:

```text
healthy
```

You can also check PostgreSQL logs:

```bash
docker compose logs postgres
```

### Port already in use

If port `8080` (the default `NGINX_PORT`) is already being used, change it in `.env`:

```env
NGINX_PORT=8081
```

Or override it directly in `docker-compose.yml`:

```yaml
ports:
  - "8082:80"
```

The application will then be available at `http://localhost:8081` (or whatever host port you picked). The nginx container still listens on port `80`; only the host port changes.

### PostgreSQL port already in use

If port `5432` is already being used on your computer, you can change the host port:

```yaml
ports:
  - "5433:5432"
```

You would then access PostgreSQL from your Windows host through port `5433`.

The FastAPI container should still connect using:

```text
postgres:5432
```

because containers communicate through the Docker network.

## Development

For development, you can mount your local project directory into the container and enable FastAPI reload.

Create a `docker-compose.dev.yml`:

```yaml
services:

  app:
    volumes:
      - .:/app

    command:
      uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the development environment:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

The application will automatically reload when Python source files change.

## Useful Docker Commands

Build the services:

```bash
docker compose build
```

Start services:

```bash
docker compose up -d
```

Stop services:

```bash
docker compose down
```

Check services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Rebuild and start:

```bash
docker compose up -d --build
```
