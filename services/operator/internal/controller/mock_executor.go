package controller

import (
	"context"

	"github.com/phuoctmse/runguard/shared/types"
)

// MockExecutor is a test double that records executed actions.
type MockExecutor struct {
	Executed []types.RemediationStep
}

// NewMockExecutor creates a new MockExecutor.
func NewMockExecutor() *MockExecutor {
	return &MockExecutor{}
}

// Execute records the action and returns nil (always succeeds).
func (m *MockExecutor) Execute(ctx context.Context, step types.RemediationStep, inc types.Incident) error {
	m.Executed = append(m.Executed, step)
	return nil
}
