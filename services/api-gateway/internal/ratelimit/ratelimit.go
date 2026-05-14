package ratelimit

import (
	"net"
	"net/http"
	"sync"

	"golang.org/x/time/rate"
)

// Limiter provides per-IP rate limiting.
type Limiter struct {
	mu       sync.Mutex
	visitors map[string]*rate.Limiter
	rate     rate.Limit
	burst    int
}

// New creates a new rate Limiter.
func New(rps float64, burst int) *Limiter {
	return &Limiter{
		visitors: make(map[string]*rate.Limiter),
		rate:     rate.Limit(rps),
		burst:    burst,
	}
}

// getLimiter returns the rate limiter for the given IP.
func (l *Limiter) getLimiter(ip string) *rate.Limiter {
	l.mu.Lock()
	defer l.mu.Unlock()

	limiter, exists := l.visitors[ip]
	if !exists {
		limiter = rate.NewLimiter(l.rate, l.burst)
		l.visitors[ip] = limiter
	}

	return limiter
}

// Limit returns middleware that rate limits by IP.
func (l *Limiter) Limit(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip, _, _ := net.SplitHostPort(r.RemoteAddr)
		limiter := l.getLimiter(ip)

		if !limiter.Allow() {
			http.Error(w, `{"error":"rate limit exceeded"}`, http.StatusTooManyRequests)
			return
		}

		next.ServeHTTP(w, r)
	})
}
