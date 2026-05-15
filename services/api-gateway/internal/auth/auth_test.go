package auth

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

func TestAuthMiddlewareValidToken(t *testing.T) {
	secret := []byte("test-secret")
	mw := NewMiddleware(secret)

	token := generateTestToken(t, secret, "user-1", time.Now().Add(1*time.Hour))

	req := httptest.NewRequest(http.MethodGet, "/api/incidents", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()

	called := false
	handler := mw.Protect(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		called = true
		userID := GetUserID(r.Context())
		if userID != "user-1" {
			t.Errorf("userID = %q, want %q", userID, "user-1")
		}
	}))

	handler.ServeHTTP(w, req)

	if !called {
		t.Error("handler was not called")
	}
	if w.Code != http.StatusOK {
		t.Errorf("status = %d, want %d", w.Code, http.StatusOK)
	}
}

func TestAuthMiddlewareMissingToken(t *testing.T) {
	secret := []byte("test-secret")
	mw := NewMiddleware(secret)

	req := httptest.NewRequest(http.MethodGet, "/api/incidents", nil)
	w := httptest.NewRecorder()

	handler := mw.Protect(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called")
	}))

	handler.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("status = %d, want %d", w.Code, http.StatusUnauthorized)
	}
}

func TestAuthMiddlewareExpiredToken(t *testing.T) {
	secret := []byte("test-secret")
	mw := NewMiddleware(secret)

	token := generateTestToken(t, secret, "user-1", time.Now().Add(-1*time.Hour))

	req := httptest.NewRequest(http.MethodGet, "/api/incidents", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()

	handler := mw.Protect(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Error("handler should not be called")
	}))

	handler.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("status = %d, want %d", w.Code, http.StatusUnauthorized)
	}
}

func generateTestToken(t *testing.T, secret []byte, userID string, expires time.Time) string {
	t.Helper()
	claims := jwt.MapClaims{
		"sub": userID,
		"exp": expires.Unix(),
		"iat": time.Now().Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := token.SignedString(secret)
	if err != nil {
		t.Fatalf("failed to sign token: %v", err)
	}
	return signed
}
