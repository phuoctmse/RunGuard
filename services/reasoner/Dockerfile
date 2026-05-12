FROM python:3.14.5-alpine3.23 as builder 

WORKDIR /app
COPY pyproject.toml  ./
COPY src/  src/
RUN pip install --no-cache-dir --target=/deps .

FROM python:3.14.5-alpine3.23
WORKDIR /app 
COPY --from=builder /deps /usr/local/lib/python3.14.5/site-packages
COPY src/  src/
EXPOSE 8082
RUN adduser -D appuser
USER appuser
CMD ["python", "-m", "uvicorn", "reasoner.main:app", "--host", "0.0.0.0", "--port", "8082"]
