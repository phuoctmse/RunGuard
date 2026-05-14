package compiler

import (
	"fmt"
	"strings"
)

// ParsedRunbook holds the parsed result of a Markdown runbook.
type ParsedRunbook struct {
	Title        string
	Scope        RunbookScope
	Severity     []string
	AllowedTools []string
	Forbidden    []string
	Diagnosis    []DiagnosisEntry
	Remediation  []ParsedStep
	Rollback     []ParsedStep
}

type RunbookScope struct {
	Namespaces []string
	Resources  []string
}

type DiagnosisEntry struct {
	Name    string
	Command string
}

type ParsedStep struct {
	Name        string
	Action      string
	Target      string
	Risk        string
	AutoApprove bool
}

// ParseMarkdown parses a Markdown runbook into a ParsedRunbook.
func ParseMarkdown(data []byte) (*ParsedRunbook, error) {
	content := string(data)
	lines := strings.Split(content, "\n")

	if len(lines) == 0 || !strings.HasPrefix(lines[0], "# ") {
		return nil, fmt.Errorf("invalid syntax: must start with # title")
	}

	rb := &ParsedRunbook{
		Title: strings.TrimPrefix(lines[0], "# "),
	}

	currentSection := ""
	currentSubsection := ""
	inCodeBlock := false
	codeBlockContent := strings.Builder{}

	for _, line := range lines[1:] {
		trimmed := strings.TrimSpace(line)

		// Code block toggle
		if strings.HasPrefix(trimmed, "```") {
			if inCodeBlock {
				// End of code block — save diagnosis entry
				if currentSection == "diagnosis" && currentSubsection != "" {
					rb.Diagnosis = append(rb.Diagnosis, DiagnosisEntry{
						Name:    currentSubsection,
						Command: strings.TrimSpace(codeBlockContent.String()),
					})
				}
				codeBlockContent.Reset()
				inCodeBlock = false
			} else {
				inCodeBlock = true
			}
			continue
		}

		if inCodeBlock {
			codeBlockContent.WriteString(line + "\n")
			continue
		}

		// Section headers (## )
		if strings.HasPrefix(trimmed, "## ") {
			currentSection = strings.ToLower(strings.TrimPrefix(trimmed, "## "))
			currentSubsection = ""
			continue
		}

		// Subsection headers (### )
		if strings.HasPrefix(trimmed, "### ") {
			currentSubsection = strings.TrimPrefix(trimmed, "### ")
			continue
		}

		// Parse content based on section
		switch currentSection {
		case "scope":
			parseScopeLine(trimmed, rb)
		case "severity":
			if trimmed != "" {
				parts := strings.Split(trimmed, ",")
				for _, p := range parts {
					rb.Severity = append(rb.Severity, strings.TrimSpace(p))
				}
			}
		case "allowed tools":
			if strings.HasPrefix(trimmed, "- ") {
				rb.AllowedTools = append(rb.AllowedTools, strings.TrimPrefix(trimmed, "- "))
			}
		case "forbidden tools":
			if strings.HasPrefix(trimmed, "- ") {
				rb.Forbidden = append(rb.Forbidden, strings.TrimPrefix(trimmed, "- "))
			}
		case "remediation":
			if strings.HasPrefix(trimmed, "- ") && currentSubsection != "" {
				idx := findStepIndex(rb.Remediation, currentSubsection)
				if idx >= 0 {
					parseAndMergeStep(&rb.Remediation[idx], trimmed)
				} else {
					newStep := ParsedStep{Name: currentSubsection}
					parseAndMergeStep(&newStep, trimmed)
					rb.Remediation = append(rb.Remediation, newStep)
				}
			}
		case "rollback":
			if strings.HasPrefix(trimmed, "- ") && currentSubsection != "" {
				idx := findStepIndex(rb.Rollback, currentSubsection)
				if idx >= 0 {
					parseAndMergeStep(&rb.Rollback[idx], trimmed)
				} else {
					newStep := ParsedStep{Name: currentSubsection}
					parseAndMergeStep(&newStep, trimmed)
					rb.Rollback = append(rb.Rollback, newStep)
				}
			}
		}
	}

	// Validate: must have rollback section [Req 1.3]
	if len(rb.Rollback) == 0 {
		return nil, fmt.Errorf("missing rollback section")
	}

	return rb, nil
}

func parseScopeLine(line string, rb *ParsedRunbook) {
	if strings.HasPrefix(line, "- Namespaces:") {
		val := strings.TrimPrefix(line, "- Namespaces:")
		parts := strings.Split(val, ",")
		for _, p := range parts {
			rb.Scope.Namespaces = append(rb.Scope.Namespaces, strings.TrimSpace(p))
		}
	}
	if strings.HasPrefix(line, "- Resources:") {
		val := strings.TrimPrefix(line, "- Resources:")
		parts := strings.Split(val, ",")
		for _, p := range parts {
			rb.Scope.Resources = append(rb.Scope.Resources, strings.TrimSpace(p))
		}
	}
}

// parseAndMergeStep parses a "- Key: Value" line and merges into the step.
func parseAndMergeStep(step *ParsedStep, line string) {
	parts := strings.SplitN(strings.TrimPrefix(line, "- "), ":", 2)
	if len(parts) != 2 {
		return
	}

	key := strings.TrimSpace(strings.ToLower(parts[0]))
	val := strings.TrimSpace(parts[1])

	switch key {
	case "action":
		step.Action = val
	case "target":
		step.Target = val
	case "risk":
		step.Risk = val
	case "autoapprove":
		step.AutoApprove = strings.ToLower(val) == "true"
	}
}

func findStepIndex(steps []ParsedStep, name string) int {
	for i, s := range steps {
		if s.Name == name {
			return i
		}
	}
	return -1
}
