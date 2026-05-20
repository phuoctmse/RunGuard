package store

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/phuoctmse/runguard/shared/types"
)

// PostgresConfig holds connection parameters for PostgreSQL.
type PostgresConfig struct {
	Host     string
	Port     string
	User     string
	Password string
	Database string
}

// PostgresStore is a PostgreSQL-backed implementation of the incident store.
type PostgresStore struct {
	pool *pgxpool.Pool
	cfg  PostgresConfig
}

// NewPostgresStore creates a PostgresStore with the given config.
func NewPostgresStore(cfg PostgresConfig) *PostgresStore {
	return &PostgresStore{cfg: cfg}
}

// NewPostgresStoreFromEnv creates a PostgresStore reading config from environment variables.
func NewPostgresStoreFromEnv() *PostgresStore {
	return &PostgresStore{
		cfg: PostgresConfig{
			Host:     getEnv("DB_HOST", "localhost"),
			Port:     getEnv("DB_PORT", "5433"),
			User:     getEnv("DB_USER", "runguard"),
			Password: getEnv("DB_PASSWORD", "runguard"),
			Database: getEnv("DB_NAME", "runguard"),
		},
	}
}

// connString builds the PostgreSQL connection string.
// DATABASE_URL env var takes precedence if set.
func (s *PostgresStore) connString() string {
	if ds := os.Getenv("DATABASE_URL"); ds != "" {
		return ds
	}
	return fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable",
		s.cfg.User, s.cfg.Password, s.cfg.Host, s.cfg.Port, s.cfg.Database)
}

// Connect initializes the connection pool and runs migrations.
func (s *PostgresStore) Connect(ctx context.Context) error {
	pool, err := pgxpool.New(ctx, s.connString())
	if err != nil {
		return fmt.Errorf("create pool: %w", err)
	}
	s.pool = pool

	if err := s.migrate(ctx); err != nil {
		return fmt.Errorf("migrate: %w", err)
	}

	return nil
}

// migrate creates the incidents table if it does not exist.
func (s *PostgresStore) migrate(ctx context.Context) error {
	_, err := s.pool.Exec(ctx, `
		CREATE TABLE IF NOT EXISTS incidents (
			id TEXT PRIMARY KEY,
			data JSONB NOT NULL,
			phase TEXT NOT NULL DEFAULT 'Pending',
			created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
			updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
		)
	`)
	return err
}

// CreateIncident stores a new incident and returns its generated ID.
func (s *PostgresStore) CreateIncident(ctx context.Context, inc types.Incident) (string, error) {
	data, err := json.Marshal(inc)
	if err != nil {
		return "", fmt.Errorf("marshal incident: %w", err)
	}

	var id string
	err = s.pool.QueryRow(ctx,
		`INSERT INTO incidents (id, data, phase) VALUES (gen_random_uuid(), $1, $2) RETURNING id`,
		string(data), string(inc.Phase),
	).Scan(&id)
	if err != nil {
		return "", fmt.Errorf("insert incident: %w", err)
	}

	return id, nil
}

// GetIncident retrieves an incident by ID.
func (s *PostgresStore) GetIncident(ctx context.Context, id string) (*types.Incident, error) {
	var data string
	err := s.pool.QueryRow(ctx, `SELECT data FROM incidents WHERE id = $1`, id).Scan(&data)
	if err == pgx.ErrNoRows {
		return nil, fmt.Errorf("incident %q not found", id)
	}
	if err != nil {
		return nil, fmt.Errorf("get incident: %w", err)
	}

	var inc types.Incident
	if err := json.Unmarshal([]byte(data), &inc); err != nil {
		return nil, fmt.Errorf("unmarshal incident: %w", err)
	}

	return &inc, nil
}

// ListIncidents returns all incidents ordered by creation time (newest first).
func (s *PostgresStore) ListIncidents(ctx context.Context) ([]types.Incident, error) {
	rows, err := s.pool.Query(ctx, `SELECT data FROM incidents ORDER BY created_at DESC`)
	if err != nil {
		return nil, fmt.Errorf("list incidents: %w", err)
	}
	defer rows.Close()

	var result []types.Incident
	for rows.Next() {
		var data string
		if err := rows.Scan(&data); err != nil {
			return nil, fmt.Errorf("scan incident: %w", err)
		}
		var inc types.Incident
		if err := json.Unmarshal([]byte(data), &inc); err != nil {
			return nil, fmt.Errorf("unmarshal incident: %w", err)
		}
		result = append(result, inc)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate incidents: %w", err)
	}

	return result, nil
}

// UpdateIncident updates an existing incident by ID.
func (s *PostgresStore) UpdateIncident(ctx context.Context, id string, inc types.Incident) error {
	data, err := json.Marshal(inc)
	if err != nil {
		return fmt.Errorf("marshal incident: %w", err)
	}

	tag, err := s.pool.Exec(ctx,
		`UPDATE incidents SET data = $1, phase = $2, updated_at = NOW() WHERE id = $3`,
		string(data), string(inc.Phase), id,
	)
	if err != nil {
		return fmt.Errorf("update incident: %w", err)
	}
	if tag.RowsAffected() == 0 {
		return fmt.Errorf("incident %q not found", id)
	}

	return nil
}

// Close shuts down the connection pool.
func (s *PostgresStore) Close() {
	if s.pool != nil {
		s.pool.Close()
	}
}

// getEnv returns the environment variable value or the fallback.
func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
