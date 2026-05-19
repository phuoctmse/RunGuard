package middleware

import (
	"net/http"
	"os"
)

// ServiceAuth returns middleware that validates X-Service-Token header.
func ServiceAuth(expectedToken string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			token := r.Header.Get("X-Service-Token")
			if token != expectedToken {
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusForbidden)
				_, _ = w.Write([]byte(`{"error":"invalid service token"}`))
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// ServiceTokenFromEnv reads service token from environment.
// Returns "dev-service-token" if SERVICE_TOKEN is not set.
func ServiceTokenFromEnv() string {
	token := os.Getenv("SERVICE_TOKEN")
	if token == "" {
		return "dev-service-token"
	}
	return token
}
