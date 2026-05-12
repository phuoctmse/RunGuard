package config

import (
	"os"
	"testing"
)

func TestLoadFromEnv(t *testing.T) {
	os.Setenv("API_GATEWAY_PORT", "9090")
	defer os.Unsetenv("API_GATEWAY_PORT")

	cfg := Load()
	if cfg.Port != "9090" {
		t.Errorf("Port = %q, want %q", cfg.Port, "9090")
	}
}

func TestDefaultPort(t *testing.T) {
	os.Unsetenv("API_GATEWAY_PORT")

	cfg := Load()
	if cfg.Port != "8080" {
		t.Errorf("Port = %q, want %q", cfg.Port, "8080")
	}
}
