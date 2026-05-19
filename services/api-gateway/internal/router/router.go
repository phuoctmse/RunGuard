package router

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/phuoctmse/runguard/shared/health"
)

// Router handles routing and proxying for the API gateway.
type Router struct {
	chi           *chi.Mux
	backendURL    string
	serviceToken  string
}

// NewRouter creates a new Router that proxies to the given backend URL.
func NewRouter(backendURL string, serviceToken string) *Router {
	r := &Router{
		chi:          chi.NewRouter(),
		backendURL:   backendURL,
		serviceToken: serviceToken,
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

	// Health — liveness + readiness
	checker := health.New("api-gateway")
	r.chi.Get("/healthz", checker.LiveHandler())
	r.chi.Get("/readyz", checker.ReadyHandler())

	// Versioned API — proxy /v1/* to backend /api/*
	r.chi.Route("/v1", func(v1 chi.Router) {
		v1.Handle("/*", r.proxyHandler("/v1", "/api"))
	})
}

func (r *Router) proxyHandler(stripPrefix, addPrefix string) http.Handler {
	target, _ := url.Parse(r.backendURL)
	return &httputil.ReverseProxy{
		Rewrite: func(pr *httputil.ProxyRequest) {
			pr.SetURL(target)
			pr.Out.URL.Path = addPrefix + strings.TrimPrefix(pr.In.URL.Path, stripPrefix)
			pr.Out.URL.RawPath = ""
			if r.serviceToken != "" {
				pr.Out.Header.Set("X-Service-Token", r.serviceToken)
			}
		},
	}
}
