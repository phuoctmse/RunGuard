package auth

import (
	"context"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
	apperrors "github.com/phuoctmse/runguard/shared/errors"
)

type contextKey string

const userIDKey contextKey = "user_id"

type Middleware struct {
	secret []byte
}

func NewMiddleware(secret []byte) *Middleware {
	return &Middleware{secret: secret}
}

// Protect returns middleware that validates JWT tokens.
func (m *Middleware) Protect(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			apperrors.WriteError(w, http.StatusUnauthorized, "missing authorization header", "UNAUTHORIZED")
			return
		}

		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			apperrors.WriteError(w, http.StatusUnauthorized, "invalid authorization format", "UNAUTHORIZED")
			return
		}

		token, err := jwt.Parse(parts[1], func(token *jwt.Token) (interface{}, error) {
			return m.secret, nil
		})
		if err != nil || !token.Valid {
			apperrors.WriteError(w, http.StatusUnauthorized, "invalid token", "UNAUTHORIZED")
			return
		}

		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			apperrors.WriteError(w, http.StatusUnauthorized, "invalid claims", "UNAUTHORIZED")
			return
		}

		userID, _ := claims.GetSubject()
		ctx := context.WithValue(r.Context(), userIDKey, userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// GetUserID extracts the user ID from the request context.
func GetUserID(ctx context.Context) string {
	if v, ok := ctx.Value(userIDKey).(string); ok {
		return v
	}
	return ""
}
