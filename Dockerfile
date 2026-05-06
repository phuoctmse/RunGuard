FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
COPY runguard/ runguard/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .
EXPOSE 8000 8501
CMD ["uvicorn", "runguard.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]