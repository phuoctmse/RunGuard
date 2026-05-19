package errors

import (
	"encoding/json"
	"net/http"
)

// ErrorResponse is the standard error envelope returned by all services.
type ErrorResponse struct {
	Error   string `json:"error"`
	Code    string `json:"code,omitempty"`
	Details string `json:"details,omitempty"`
}

// WriteError writes a standardized JSON error response.
func WriteError(w http.ResponseWriter, status int, message string, code string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(ErrorResponse{
		Error: message,
		Code:  code,
	})
}

// WriteValidationError writes a 400 validation error.
func WriteValidationError(w http.ResponseWriter, details string) {
	WriteError(w, http.StatusBadRequest, "validation failed", "VALIDATION_ERROR")
}

// WriteNotFound writes a 404 not found error.
func WriteNotFound(w http.ResponseWriter, resource string) {
	WriteError(w, http.StatusNotFound, resource+" not found", "NOT_FOUND")
}

// WriteInternalError writes a 500 internal server error.
func WriteInternalError(w http.ResponseWriter) {
	WriteError(w, http.StatusInternalServerError, "internal server error", "INTERNAL_ERROR")
}
