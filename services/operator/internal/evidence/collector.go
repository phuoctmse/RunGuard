package evidence

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
	"strings"

	"github.com/phuoctmse/runguard/shared/types"
)

// Collector gathers evidence by running diagnostic commands.
type Collector struct{}

// NewCollector creates a new Collector.
func NewCollector() *Collector {
	return &Collector{}
}

// Collect runs diagnosis steps and returns the output keyed by step name.
func (c *Collector) Collect(ctx context.Context, inc types.Incident, steps []types.DiagnosisStep) (map[string]string, error) {
	evidence := make(map[string]string)

	for _, step := range steps {
		// Template substitution
		cmd := step.Command
		cmd = strings.ReplaceAll(cmd, "{{.PodName}}", inc.Workload)
		cmd = strings.ReplaceAll(cmd, "{{.Namespace}}", inc.Namespace)

		output, err := c.runCommand(ctx, cmd)
		if err != nil {
			evidence[step.Name] = fmt.Sprintf("ERROR: %v", err)
			continue
		}
		evidence[step.Name] = output
	}

	return evidence, nil
}

// runCommand executes a shell command and returns its stdout.
func (c *Collector) runCommand(ctx context.Context, cmd string) (string, error) {
	parts := strings.Fields(cmd)
	if len(parts) == 0 {
		return "", fmt.Errorf("empty command")
	}

	execCmd := exec.CommandContext(ctx, parts[0], parts[1:]...)
	var stdout, stderr bytes.Buffer
	execCmd.Stdout = &stdout
	execCmd.Stderr = &stderr

	if err := execCmd.Run(); err != nil {
		return "", fmt.Errorf("%s: %s", err, stderr.String())
	}

	return stdout.String(), nil
}
