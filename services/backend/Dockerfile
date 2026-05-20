FROM golang:1.26-alpine as builder

WORKDIR /app
ENV GOWORK=off
COPY go.work  ./
COPY shared/  ./shared/
COPY services/backend/go.mod  ./services/backend/
RUN cd services/backend && go mod download 

COPY services/backend/  ./services/backend/
RUN cd services/backend && CGO_ENABLED=0 GOOS=linux go build -o /bin/backend ./cmd/main.go

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /bin/backend /bin/backend
USER 65534:65534
EXPOSE 8081
ENTRYPOINT ["/bin/backend"]