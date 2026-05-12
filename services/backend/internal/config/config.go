package config

import "os"

type Config struct {
	Port string
}

func LoadConfig() *Config {
	port := os.Getenv("BACKEND_PORT")
	if port == "" {
		port = "8081"
	}
	return &Config{Port: port}
}
