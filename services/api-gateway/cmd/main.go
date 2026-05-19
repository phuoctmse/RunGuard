package main

import (
	"api-gateway/internal/auth"
	"api-gateway/internal/config"
	"api-gateway/internal/ratelimit"
	"api-gateway/internal/router"
	"context"
	"fmt"
	"net/http"
	"os"

	"github.com/phuoctmse/runguard/shared/logger"
	"github.com/phuoctmse/runguard/shared/metrics"
	"github.com/phuoctmse/runguard/shared/middleware"
	"github.com/phuoctmse/runguard/shared/server"
	"github.com/phuoctmse/runguard/shared/tracing"
)

func main() {
	cfg := config.Load()
	log := logger.New("api-gateway")

	// Tracing
	tp, err := tracing.InitTracer("api-gateway")
	if err != nil {
		log.Error("failed to init tracer", "error", err)
	} else {
		defer func() { _ = tp.Shutdown(context.Background()) }()
	}

	// Metrics
	metricsHandler := metrics.NewHandler("api-gateway")

	backendURL := os.Getenv("BACKEND_URL")
	if backendURL == "" {
		backendURL = "http://localhost:8081"
	}

	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "dev-secret-change-in-production"
	}

	serviceToken := middleware.ServiceTokenFromEnv()
	r := router.NewRouter(backendURL, serviceToken)
	authMw := auth.NewMiddleware([]byte(jwtSecret))
	rateLimiter := ratelimit.New(100, 200) // 100 req/s, burst 200

	// Apply middleware to protected routes
	protected := authMw.Protect(r)
	limited := rateLimiter.Limit(protected)

	// Combine: /metrics endpoint + main handler with tracing + metrics middleware
	mux := http.NewServeMux()
	mux.Handle("/metrics", metricsHandler.MetricsHandler())
	mux.Handle("/", tracing.Middleware("api-gateway")(metricsHandler.Middleware(limited)))

	addr := fmt.Sprintf(":%s", cfg.Port)
	srv := server.New(addr, log)
	srv.ListenAndServe(mux)
}
