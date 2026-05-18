package server

import (
	"context"
	"net/http"
	"testing"
	"time"
)

func TestServerGracefulShutdown(t *testing.T) {
	srv := New(":0")

	done := srv.ListenAndServeAsync(http.NewServeMux())

	time.Sleep(100 * time.Millisecond)

	srv.Shutdown(context.Background())

	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Fatal("server did not shut down within timeout")
	}
}
