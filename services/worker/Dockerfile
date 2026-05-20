FROM golang:1.26-alpine AS builder
WORKDIR /app
ENV GOWORK=off
COPY shared/ ./shared/
COPY services/worker/go.mod ./services/worker/
RUN cd services/worker && go mod download

COPY services/worker/ ./services/worker/
RUN cd services/worker && go build -o /worker ./cmd/main.go

FROM gcr.io/distroless/static-debian12:latest
COPY --from=builder /worker /usr/local/bin/worker
ENTRYPOINT ["worker"]