FROM golang:1.26-alpine as builder

WORKDIR /app
ENV GOWORK=off
COPY go.work  ./
COPY shared/  ./shared/
COPY services/api-gateway/go.mod  ./services/api-gateway/
RUN cd services/api-gateway && go mod download 

COPY services/api-gateway/  ./services/api-gateway/
RUN cd services/api-gateway && CGO_ENABLED=0 GOOS=linux go build -o /bin/api-gateway ./cmd/main.go

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /bin/api-gateway /bin/api-gateway
USER 65534:65534
EXPOSE 8080
ENTRYPOINT ["/bin/api-gateway"]