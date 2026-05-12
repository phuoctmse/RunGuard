FROM golang:1.26-alpine as builder

WORKDIR /app
COPY go.work  ./
COPY shared/types/  ./shared/types/
COPY services/api-gateway/go.mod  ./services/api-gateway/
RUN cd services/api-gateway && go mod download 

COPY services/api-gateway/  ./services/api-gateway/
RUN cd services/api-gateway && CGO_ENABLED=0 GOOS=linux go build -o /bin/api-gateway ./cmd/main.go

FROM gcr.io/distroless/static-debian12
COPY --from=builder /bin/api-gateway /bin/api-gateway
RUN adduser -D appuser
USER appuser
EXPOSE 8080
ENTRYPOINT ["/bin/api-gateway"] 