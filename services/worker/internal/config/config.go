package config

import "os"

type Config struct {
	Port       string
	NATSURL    string
	BackendURL string
}

func Load() Config {
	return Config{
		Port:       getEnv("PORT", "8083"),
		NATSURL:    getEnv("NATS_URL", "nats://localhost:4222"),
		BackendURL: getEnv("BACKEND_URL", "http://localhost:8081"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
