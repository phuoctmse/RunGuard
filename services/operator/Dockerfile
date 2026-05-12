FROM golang:1.26-alpine as builder

WORKDIR /app
COPY go.work  ./
COPY shared/types/  ./shared/types/
COPY services/operator/go.mod  ./services/operator/
RUN cd services/operator && go mod download 

COPY services/operator/  ./services/operator/
RUN cd services/operator && CGO_ENABLED=0 GOOS=linux go build -o /bin/operator ./cmd/main.go

FROM gcr.io/distroless/static-debian12
COPY --from=builder /bin/operator /bin/operator
RUN adduser -D appuser
USER appuser
EXPOSE 9090
ENTRYPOINT ["/bin/operator"] 