FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RADAR_DATA_DIR=/app/data

WORKDIR /app

# The generated plan dashboard reads origin/master with git at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root runtime user and the persistent SQLite directory.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip \
    && pip install .

COPY app.py desktop.py plan_dashboard*.py ./
COPY PROJECT_PLAN.md ./
COPY src ./src

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]

FROM runtime AS test

USER root
RUN pip install ".[test]"
COPY tests ./tests
RUN chown -R appuser:appuser /app
USER appuser

CMD ["pytest", "-q"]

FROM runtime AS production
