package main

import (
	"context"
	"fmt"
	"net/http"
	"strings"

	"github.com/phuoctmse/runguard/services/backend/internal/audit"
	"github.com/phuoctmse/runguard/services/backend/internal/config"
	"github.com/phuoctmse/runguard/services/backend/internal/handler"
	"github.com/phuoctmse/runguard/services/backend/internal/store"
	"github.com/phuoctmse/runguard/shared/health"
	"github.com/phuoctmse/runguard/shared/logger"
	"github.com/phuoctmse/runguard/shared/metrics"
	"github.com/phuoctmse/runguard/shared/middleware"
	"github.com/phuoctmse/runguard/shared/server"
	"github.com/phuoctmse/runguard/shared/tracing"
)

func main() {
	cfg := config.LoadConfig()
	log := logger.New("backend")

	// Tracing
	tp, err := tracing.InitTracer("backend")
	if err != nil {
		log.Error("failed to init tracer", "error", err)
	} else {
		defer func() { _ = tp.Shutdown(context.Background()) }()
	}

	// Metrics
	metricsHandler := metrics.NewHandler("backend")

	h := handler.New()
	appStore := store.NewStore()
	auditStore := audit.NewMemoryAuditStore()
	auditHandler := handler.NewWithAuditStore(auditStore)

	mux := http.NewServeMux()

	// Health — liveness + readiness
	checker := health.New("backend")
	checker.AddCheck("store", appStore.HealthCheck)
	mux.HandleFunc("/healthz", checker.LiveHandler())
	mux.HandleFunc("/readyz", checker.ReadyHandler())

	// Metrics
	mux.Handle("/metrics", metricsHandler.MetricsHandler())

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
		if strings.HasPrefix(r.URL.Path, "/healthz") || strings.HasPrefix(r.URL.Path, "/readyz") {
			mux.ServeHTTP(w, r)
			return
		}
		authMw(mux).ServeHTTP(w, r)
	})

	// Wrap with tracing + metrics middleware
	traced := tracing.Middleware("backend")(metricsHandler.Middleware(handler))

	addr := fmt.Sprintf(":%s", cfg.Port)
	srv := server.New(addr, log)
	srv.ListenAndServe(traced)
}
