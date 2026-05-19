package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/phuoctmse/runguard/services/operator/internal/config"
	"github.com/phuoctmse/runguard/services/operator/internal/controller"
	"github.com/phuoctmse/runguard/services/operator/internal/executor"
	"github.com/phuoctmse/runguard/services/operator/internal/webhook"
	"github.com/phuoctmse/runguard/shared/health"
	"github.com/phuoctmse/runguard/shared/logger"
	"github.com/phuoctmse/runguard/shared/metrics"
	"github.com/phuoctmse/runguard/shared/server"
	"github.com/phuoctmse/runguard/shared/tracing"
	"github.com/phuoctmse/runguard/shared/types"
)

func main() {
	cfg := config.Load()
	log := logger.New("operator")

	// Tracing
	tp, err := tracing.InitTracer("operator")
	if err != nil {
		log.Error("failed to init tracer", "error", err)
	} else {
		defer func() { _ = tp.Shutdown(context.Background()) }()
	}

	// Metrics
	metricsHandler := metrics.NewHandler("operator")

	// Initialize components
	store := controller.NewMemoryIncidentStore()
	runbooks := []types.Runbook{
		{
			AlertName: "PodCrashLooping",
			Severity:  []string{"critical", "warning"},
			Diagnosis: []types.DiagnosisStep{
				{Name: "check_logs", Command: "kubectl logs {{.PodName}} -n {{.Namespace}} --tail=100"},
			},
			Remediation: []types.RemediationStep{
				{Name: "restart", Action: "restart", Target: "{{.PodName}}", Risk: "low", AutoApprove: true},
			},
		},
	}
	exec := executor.New()
	policy := types.Policy{}
	reconciler := controller.NewReconcilerWithPolicy(store, runbooks, exec, policy)

	// HTTP handlers
	mux := http.NewServeMux()

	// Health — liveness + readiness
	checker := health.New("operator")
	checker.AddCheck("executor", func() error { return nil })
	mux.HandleFunc("/healthz", checker.LiveHandler())
	mux.HandleFunc("/readyz", checker.ReadyHandler())

	// Metrics
	mux.Handle("/metrics", metricsHandler.MetricsHandler())

	mux.HandleFunc("/webhook/alertmanager", func(w http.ResponseWriter, r *http.Request) {
		inc, err := webhook.ParseWebhook(r)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err), http.StatusBadRequest)
			return
		}

		id, err := store.Create(r.Context(), *inc)
		if err != nil {
			http.Error(w, `{"error":"failed to create incident"}`, http.StatusInternalServerError)
			return
		}

		// Reconcile in background
		go func() {
			if err := reconciler.Reconcile(r.Context(), id); err != nil {
				log.Error("reconcile failed", "id", id, "error", err)
			}
		}()

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		_ = json.NewEncoder(w).Encode(map[string]string{"id": id, "status": "received"})
	})

	// Wrap with tracing + metrics middleware
	traced := tracing.Middleware("operator")(metricsHandler.Middleware(mux))

	addr := fmt.Sprintf(":%s", cfg.AlertmanagerWebhookPort)
	srv := server.New(addr, log)
	srv.ListenAndServe(traced)
}
