package router

import (
	"net/http"
	"net/http/httputil"
	"net/url"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// Router handles routing and proxying for the API gateway.
type Router struct {
	chi        *chi.Mux
	backendURL string
}

// NewRouter creates a new Router that proxies to the given backend URL.
func NewRouter(backendURL string) *Router {
	r := &Router{
		chi:        chi.NewRouter(),
		backendURL: backendURL,
	}
	r.setupRoutes()
	return r
}

// ServeHTTP implements http.Handler.
func (r *Router) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	r.chi.ServeHTTP(w, req)
}

func (r *Router) setupRoutes() {
	r.chi.Use(middleware.Logger)
	r.chi.Use(middleware.Recoverer)

	// Health
	r.chi.Get("/healthz", func(w http.ResponseWriter, req *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"ok"}`))
	})

	// Proxy all /api/* to backend
	r.chi.Handle("/api/*", r.proxyHandler())
}

func (r *Router) proxyHandler() http.Handler {
	target, _ := url.Parse(r.backendURL)
	proxy := httputil.NewSingleHostReverseProxy(target)
	return proxy
}
