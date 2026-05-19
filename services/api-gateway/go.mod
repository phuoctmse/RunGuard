module api-gateway

go 1.25.0

replace github.com/phuoctmse/runguard/shared/types => ../../shared/types

replace github.com/phuoctmse/runguard/shared/logger => ../../shared/logger

replace github.com/phuoctmse/runguard/shared/server => ../../shared/server

replace github.com/phuoctmse/runguard/shared/middleware => ../../shared/middleware

require (
	github.com/phuoctmse/runguard/shared/logger v0.0.0
	github.com/phuoctmse/runguard/shared/middleware v0.0.0
	github.com/phuoctmse/runguard/shared/server v0.0.0
)

require (
	github.com/go-chi/chi/v5 v5.2.5 // indirect
	github.com/golang-jwt/jwt/v5 v5.3.1 // indirect
	golang.org/x/time v0.15.0 // indirect
)
