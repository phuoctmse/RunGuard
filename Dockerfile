FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .
COPY runguard/ runguard/
EXPOSE 8000
CMD ["uvicorn", "runguard.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]