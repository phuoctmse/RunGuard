module github.com/phuoctmse/runguard/services/operator

go 1.25

require (
	github.com/phuoctmse/runguard/shared/types v0.0.0
	github.com/phuoctmse/runguard/shared/server v0.0.0
)

replace github.com/phuoctmse/runguard/shared/types => ../../shared/types

replace github.com/phuoctmse/runguard/shared/server => ../../shared/server
