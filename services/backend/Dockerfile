FROM golang:1.26-alpine as builder

WORKDIR /app
COPY go.work  ./
COPY shared/types/  ./shared/types/
COPY services/backend/go.mod  ./services/backend/
RUN cd services/backend && go mod download 

COPY services/backend/  ./services/backend/
RUN cd services/backend && CGO_ENABLED=0 GOOS=linux go build -o /bin/backend ./cmd/main.go

FROM gcr.io/distroless/static-debian12
COPY --from=builder /bin/backend /bin/backend
RUN adduser -D appuser
USER appuser
EXPOSE 8081
ENTRYPOINT ["/bin/backend"] 