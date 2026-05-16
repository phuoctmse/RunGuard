package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/phuoctmse/runguard/services/backend/internal/audit"
	"github.com/phuoctmse/runguard/services/backend/internal/config"
	"github.com/phuoctmse/runguard/services/backend/internal/handler"
)

func main() {
	cfg := config.LoadConfig()
	h := handler.New()
	auditStore := audit.NewMemoryAuditStore()
	auditHandler := handler.NewWithAuditStore(auditStore)

	mux := http.NewServeMux()

	// Health
	mux.HandleFunc("/healthz", h.Healthz)

	// Incidents
	mux.HandleFunc("/api/incidents", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			h.ListIncidents(w, r)
		case http.MethodPost:
			h.CreateIncident(w, r)
		default:
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/api/incidents/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet {
			h.GetIncident(w, r)
		} else {
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		}
	})

	// Approval
	mux.HandleFunc("/api/incidents/", func(w http.ResponseWriter, r *http.Request) {
		// This is handled by the router above for GET
		// For approve/reject, we need path-based routing
	})

	// Runbooks
	mux.HandleFunc("/api/runbooks", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			h.ListRunbooks(w, r)
		case http.MethodPost:
			h.CreateRunbook(w, r)
		default:
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/api/audit/", auditHandler.GetAuditTrail)

	addr := fmt.Sprintf(":%s", cfg.Port)
	log.Printf("backend listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("server failed: %v", err)
	}

}
