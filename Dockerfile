FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --create-home crea /home/appuser. Sin esto, `uv run` falla con
# "Permission denied" al intentar inicializar /home/appuser/.cache/uv
# porque appuser no tiene home directory (default de `useradd --system`).
RUN groupadd --system appgroup && useradd --system --create-home --gid appgroup appuser \
    && pip install --no-cache-dir uv

# Copy only dependency manifests first for better Docker layer caching.
# Dependencies are installed before the rest of the source, so source-only
# changes don't bust the dependency-install layer.
COPY pyproject.toml uv.lock ./

# Install production dependencies (dev group excluded).
# --frozen pins to uv.lock exactly; CI fails the build if pyproject.toml and
# uv.lock diverge.
RUN uv sync --frozen --no-dev

COPY . .

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)"

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
