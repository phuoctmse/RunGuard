package metrics

import (
	"net/http"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type Handler struct {
	requestsTotal   *prometheus.CounterVec
	requestDuration *prometheus.HistogramVec
	registry        *prometheus.Registry
	handler         http.Handler
}

func NewHandler(service string) *Handler {
	requestsTotal := prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total HTTP requests",
		},
		[]string{"method", "path", "status"},
	)

	requestDuration := prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "path"},
	)

	reg := prometheus.NewRegistry()
	reg.MustRegister(requestsTotal, requestDuration)

	return &Handler{
		requestsTotal:   requestsTotal,
		requestDuration: requestDuration,
		registry:        reg,
		handler:         promhttp.HandlerFor(reg, promhttp.HandlerOpts{}),
	}
}

func (h *Handler) MetricsHandler() http.Handler {
	return h.handler
}

func (h *Handler) RecordRequest(method, path string, status int) {
	h.requestsTotal.WithLabelValues(method, path, strconv.Itoa(status)).Inc()
}

// statusRecorder wraps ResponseWriter to capture the status code.
type statusRecorder struct {
	http.ResponseWriter
	status int
}

func (sr *statusRecorder) WriteHeader(code int) {
	sr.status = code
	sr.ResponseWriter.WriteHeader(code)
}

// Middleware returns HTTP middleware that records metrics.
func (h *Handler) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		sr := &statusRecorder{ResponseWriter: w, status: http.StatusOK}
		next.ServeHTTP(sr, r)
		duration := time.Since(start).Seconds()

		h.requestsTotal.WithLabelValues(r.Method, r.URL.Path, strconv.Itoa(sr.status)).Inc()
		h.requestDuration.WithLabelValues(r.Method, r.URL.Path).Observe(duration)
	})
}
