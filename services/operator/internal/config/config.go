package config

import "os"

type Config struct {
	AlertmanagerWebhookPort string
}

func Load() *Config {
	port := os.Getenv("OPERATOR_WEBHOOK_PORT")
	if port == "" {
		port = "9090"
	}
	return &Config{AlertmanagerWebhookPort: port}
}
