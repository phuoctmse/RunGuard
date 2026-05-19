package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestServiceAuthValidToken(t *testing.T) {
	mw := ServiceAuth("shared-secret-key")

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("X-Service-Token", "shared-secret-key")
	w := httptest.NewRecorder()

	called := false
	handler := mw(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		called = true
	}))

	handler.ServeHTTP(w, req)

	if !called {
		t.Error("handler should be called with valid token")
	}
}

func TestServiceAuthInvalidToken(t *testing.T) {
	mw := ServiceAuth("shared-secret-key")

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("X-Service-Token", "wrong-token")
	w := httptest.NewRecorder()

	handler := mw(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called")
	}))

	handler.ServeHTTP(w, req)

	if w.Code != http.StatusForbidden {
		t.Errorf("status = %d, want %d", w.Code, http.StatusForbidden)
	}
}

func TestServiceAuthMissingToken(t *testing.T) {
	mw := ServiceAuth("shared-secret-key")

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	handler := mw(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called")
	}))

	handler.ServeHTTP(w, req)

	if w.Code != http.StatusForbidden {
		t.Errorf("status = %d, want %d", w.Code, http.StatusForbidden)
	}
}
