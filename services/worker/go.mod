module github.com/phuoctmse/runguard/services/worker

go 1.25.0

require github.com/phuoctmse/runguard/shared/types v0.0.0

require (
	github.com/klauspost/compress v1.18.5 // indirect
	github.com/nats-io/nats.go v1.52.0 // indirect
	github.com/nats-io/nkeys v0.4.15 // indirect
	github.com/nats-io/nuid v1.0.1 // indirect
	golang.org/x/crypto v0.49.0 // indirect
	golang.org/x/sys v0.42.0 // indirect
)

replace github.com/phuoctmse/runguard/shared/types => ../../shared/types
