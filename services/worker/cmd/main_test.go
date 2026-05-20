package main

import (
	"testing"
)

func TestWorkerConfigLoad(t *testing.T) {
	cfg := loadConfig()
	if cfg.NATSURL == "" {
		t.Error("NATSURL should have default")
	}
	if cfg.BackendURL == "" {
		t.Error("BackendURL should have default")
	}
	if cfg.Port == "" {
		t.Error("Port should have default")
	}
}
