package middleware

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	"github.com/go-playground/validator/v10"
)

var validate = validator.New()

// ValidateBody decodes the request body into T and validates it.
// Returns 400 with error details if JSON is invalid or validation fails.
func ValidateBody[T any](next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var body T
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			_, _ = fmt.Fprintf(w, `{"error":"invalid JSON: %s"}`, err.Error())
			return
		}

		if err := validate.Struct(body); err != nil {
			errors := err.(validator.ValidationErrors)
			msgs := make([]string, 0, len(errors))
			for _, e := range errors {
				msgs = append(msgs, fmt.Sprintf("%s: %s", e.Field(), e.Tag()))
			}
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusBadRequest)
			_, _ = fmt.Fprintf(w, `{"error":"validation failed: %s"}`, strings.Join(msgs, ", "))
			return
		}

		next.ServeHTTP(w, r)
	})
}
