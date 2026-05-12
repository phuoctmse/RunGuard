package main

import (
	"backend/internal/config"
	"backend/internal/handler"
	"fmt"
	"log"
	"net/http"
)

func main() {
	cfg := config.LoadConfig()
	h := handler.New()

	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", h.Health)

	addr := fmt.Sprintf(":%s", cfg.Port)
	log.Printf("backend listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}
