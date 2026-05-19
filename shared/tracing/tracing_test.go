package tracing

import (
	"context"
	"testing"

	"go.opentelemetry.io/otel"
)

func TestTracerProviderInitialization(t *testing.T) {
	tp, err := InitTracer("test-service")
	if err != nil {
		t.Fatalf("InitTracer failed: %v", err)
	}
	defer func() { _ = tp.Shutdown(context.Background()) }()

	tracer := otel.Tracer("test-service")
	_, span := tracer.Start(context.Background(), "test-operation")
	defer span.End()

	if span.SpanContext().TraceID().IsValid() == false {
		t.Error("span should have valid trace ID")
	}
}
