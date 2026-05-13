package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/phuoctmse/runguard/services/backend/internal/config"
	"github.com/phuoctmse/runguard/services/backend/internal/handler"
)

func main() {
	cfg := config.LoadConfig()
	h := handler.New()

	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", h.Healthz)

	addr := fmt.Sprintf(":%s", cfg.Port)
	log.Printf("backend listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}
