package errors

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestWriteError(t *testing.T) {
	w := httptest.NewRecorder()
	WriteError(w, http.StatusNotFound, "incident not found", "INCIDENT_NOT_FOUND")

	if w.Code != http.StatusNotFound {
		t.Errorf("status = %d, want %d", w.Code, http.StatusNotFound)
	}

	ct := w.Header().Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("content-type = %q, want application/json", ct)
	}

	var resp ErrorResponse
	if err := json.NewDecoder(w.Body).Decode(&resp); err != nil {
		t.Fatalf("decode: %v", err)
	}

	if resp.Error != "incident not found" {
		t.Errorf("error = %q, want %q", resp.Error, "incident not found")
	}
	if resp.Code != "INCIDENT_NOT_FOUND" {
		t.Errorf("code = %q, want %q", resp.Code, "INCIDENT_NOT_FOUND")
	}
}

func TestWriteValidationError(t *testing.T) {
	w := httptest.NewRecorder()
	WriteValidationError(w, "name is required")

	if w.Code != http.StatusBadRequest {
		t.Errorf("status = %d, want %d", w.Code, http.StatusBadRequest)
	}

	var resp ErrorResponse
	if err := json.NewDecoder(w.Body).Decode(&resp); err != nil {
		t.Fatalf("decode: %v", err)
	}

	if resp.Code != "VALIDATION_ERROR" {
		t.Errorf("code = %q, want %q", resp.Code, "VALIDATION_ERROR")
	}
}

func TestWriteNotFound(t *testing.T) {
	w := httptest.NewRecorder()
	WriteNotFound(w, "runbook")

	if w.Code != http.StatusNotFound {
		t.Errorf("status = %d, want %d", w.Code, http.StatusNotFound)
	}

	var resp ErrorResponse
	if err := json.NewDecoder(w.Body).Decode(&resp); err != nil {
		t.Fatalf("decode: %v", err)
	}

	if resp.Error != "runbook not found" {
		t.Errorf("error = %q, want %q", resp.Error, "runbook not found")
	}
	if resp.Code != "NOT_FOUND" {
		t.Errorf("code = %q, want %q", resp.Code, "NOT_FOUND")
	}
}

func TestWriteInternalError(t *testing.T) {
	w := httptest.NewRecorder()
	WriteInternalError(w)

	if w.Code != http.StatusInternalServerError {
		t.Errorf("status = %d, want %d", w.Code, http.StatusInternalServerError)
	}

	var resp ErrorResponse
	if err := json.NewDecoder(w.Body).Decode(&resp); err != nil {
		t.Fatalf("decode: %v", err)
	}

	if resp.Code != "INTERNAL_ERROR" {
		t.Errorf("code = %q, want %q", resp.Code, "INTERNAL_ERROR")
	}
}
