package main

import (
	"fmt"
	"net/http"
	"strings"

	"github.com/phuoctmse/runguard/services/backend/internal/audit"
	"github.com/phuoctmse/runguard/services/backend/internal/config"
	"github.com/phuoctmse/runguard/services/backend/internal/handler"
	"github.com/phuoctmse/runguard/shared/logger"
	"github.com/phuoctmse/runguard/shared/middleware"
	"github.com/phuoctmse/runguard/shared/server"
)

func main() {
	cfg := config.LoadConfig()
	log := logger.New("backend")
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

	// Service auth — skip for health check
	serviceToken := middleware.ServiceTokenFromEnv()
	authMw := middleware.ServiceAuth(serviceToken)
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/healthz") {
			mux.ServeHTTP(w, r)
			return
		}
		authMw(mux).ServeHTTP(w, r)
	})

	addr := fmt.Sprintf(":%s", cfg.Port)
	srv := server.New(addr, log)
	srv.ListenAndServe(handler)
}
