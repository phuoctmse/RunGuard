package server

import (
	"context"
	"log/slog"
	"net/http"
	"os/signal"
	"syscall"
	"time"
)

type Server struct {
	addr   string
	http   *http.Server
	logger *slog.Logger
}

func New(addr string, logger *slog.Logger) *Server {
	return &Server{addr: addr, logger: logger}
}

func (s *Server) ListenAndServe(handler http.Handler) {
	s.http = &http.Server{
		Addr:         s.addr,
		Handler:      handler,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()

	go func() {
		s.logger.Info("server listening", "addr", s.addr)
		if err := s.http.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			s.logger.Error("server failed", "error", err)
		}
	}()

	<-ctx.Done()
	s.logger.Info("shutting down gracefully...")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := s.http.Shutdown(shutdownCtx); err != nil {
		s.logger.Error("shutdown failed", "error", err)
	}
	s.logger.Info("server stopped")
}

func (s *Server) ListenAndServeAsync(handler http.Handler) <-chan struct{} {
	s.http = &http.Server{
		Addr:         s.addr,
		Handler:      handler,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	done := make(chan struct{})
	go func() {
		s.logger.Info("server listening", "addr", s.addr)
		if err := s.http.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			s.logger.Error("server failed", "error", err)
		}
		close(done)
	}()

	return done
}

func (s *Server) Shutdown(ctx context.Context) error {
	return s.http.Shutdown(ctx)
}
