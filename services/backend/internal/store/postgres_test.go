package store

import (
	"testing"
)

func TestPostgresStoreConnectionString(t *testing.T) {
	cfg := PostgresConfig{
		Host:     "localhost",
		Port:     "5433",
		User:     "runguard",
		Password: "runguard",
		Database: "runguard",
	}

	s := NewPostgresStore(cfg)
	if s.connString() != "postgres://runguard:runguard@localhost:5433/runguard?sslmode=disable" {
		t.Errorf("connString = %q", s.connString())
	}
}

func TestPostgresStoreConnectionStringFromEnv(t *testing.T) {
	t.Setenv("DATABASE_URL", "postgres://user:pass@db:5432/mydb?sslmode=require")

	s := NewPostgresStoreFromEnv()
	if s.connString() != "postgres://user:pass@db:5432/mydb?sslmode=require" {
		t.Errorf("connString = %q", s.connString())
	}
}
