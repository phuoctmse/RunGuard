module github.com/phuoctmse/runguard/services/backend

go 1.25

require (
	github.com/phuoctmse/runguard/shared/logger v0.0.0
	github.com/phuoctmse/runguard/shared/types v0.0.0
	github.com/phuoctmse/runguard/shared/server v0.0.0
)

replace github.com/phuoctmse/runguard/shared/logger => ../../shared/logger

replace github.com/phuoctmse/runguard/shared/types => ../../shared/types

replace github.com/phuoctmse/runguard/shared/server => ../../shared/server

replace github.com/phuoctmse/runguard/shared/middleware => ../../shared/middleware
