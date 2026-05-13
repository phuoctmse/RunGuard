package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"operator/internal/config"
	"operator/internal/controller"
	"operator/internal/executor"
	"operator/internal/webhook"

	"github.com/phuoctmse/runguard/shared/types"
)

func main() {
	cfg := config.Load()

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
	reconciler := controller.NewReconciler(store, runbooks, exec)

	// HTTP handlers
	mux := http.NewServeMux()

	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"status":"ok"}`)
	})

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
				log.Printf("reconcile %s failed: %v", id, err)
			}
		}()

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(map[string]string{"id": id, "status": "received"})
	})

	addr := fmt.Sprintf(":%s", cfg.AlertmanagerWebhookPort)
	log.Printf("operator listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}
