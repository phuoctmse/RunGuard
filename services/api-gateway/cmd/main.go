package main

import (
	"api-gateway/internal/auth"
	"api-gateway/internal/config"
	"api-gateway/internal/ratelimit"
	"api-gateway/internal/router"
	"fmt"
	"os"

	"github.com/phuoctmse/runguard/shared/logger"
	"github.com/phuoctmse/runguard/shared/server"
)

func main() {
	cfg := config.Load()
	log := logger.New("api-gateway")

	backendURL := os.Getenv("BACKEND_URL")
	if backendURL == "" {
		backendURL = "http://localhost:8081"
	}

	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "dev-secret-change-in-production"
	}

	r := router.NewRouter(backendURL)
	authMw := auth.NewMiddleware([]byte(jwtSecret))
	rateLimiter := ratelimit.New(100, 200) // 100 req/s, burst 200

	// Apply middleware to protected routes
	protected := authMw.Protect(r)
	limited := rateLimiter.Limit(protected)

	addr := fmt.Sprintf(":%s", cfg.Port)
	srv := server.New(addr, log)
	srv.ListenAndServe(limited)
}
