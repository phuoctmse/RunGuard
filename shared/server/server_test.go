package server

import (
	"context"
	"log/slog"
	"net/http"
	"testing"
	"time"
)

func TestServerGracefulShutdown(t *testing.T) {
	srv := New(":0", slog.Default())

	done := srv.ListenAndServeAsync(http.NewServeMux())

	time.Sleep(100 * time.Millisecond)

	if err := srv.Shutdown(context.Background()); err != nil {
		t.Fatalf("shutdown failed: %v", err)
	}

	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Fatal("server did not shut down within timeout")
	}
}
