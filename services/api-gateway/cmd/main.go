package main

import (
	"api-gateway/internal/config"
	"api-gateway/internal/handler"
	"fmt"
	"log"
	"net/http"
)

func main() {
	cfg := config.Load()
	h := handler.New()

	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", h.Healthz)
	mux.HandleFunc("/readyz", h.Readyz)

	addr := fmt.Sprintf(":%s", cfg.Port)
	log.Printf("api-gateway listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}
