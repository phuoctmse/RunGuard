FROM python:3.14.5-alpine3.23

WORKDIR /app
COPY services/reasoner/pyproject.toml ./
COPY services/reasoner/src/ src/
RUN pip install --no-cache-dir .
EXPOSE 8082
RUN adduser -D appuser
USER appuser
CMD ["python", "-m", "uvicorn", "reasoner.main:app", "--host", "0.0.0.0", "--port", "8082"]
