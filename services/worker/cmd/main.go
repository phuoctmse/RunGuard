package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/phuoctmse/runguard/services/worker/internal/config"
	"github.com/phuoctmse/runguard/services/worker/internal/processor"
	"github.com/phuoctmse/runguard/services/worker/internal/subscriber"
)

func main() {
	cfg := loadConfig()

	proc := processor.New(processor.Config{BackendURL: cfg.BackendURL})

	sub := subscriber.NewSubscriber(subscriber.Config{
		URL: cfg.NATSURL,
	})
	defer sub.Close()

	if err := sub.Connect(); err != nil {
		log.Fatalf("failed to connect to NATS: %v", err)
	}

	if err := sub.Subscribe(func(msg []byte) {
		if err := proc.HandleIncident(msg); err != nil {
			log.Printf("failed to process incident: %v", err)
		}
	}); err != nil {
		log.Fatalf("failed to subscribe: %v", err)
	}

	log.Printf("worker connected to NATS at %s, listening on incidents.new", cfg.NATSURL)

	// Wait for shutdown signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	log.Println("worker shutting down")
}

// loadConfig wraps config.Load for testability.
func loadConfig() config.Config {
	return config.Load()
}
