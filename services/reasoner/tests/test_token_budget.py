import pytest

from reasoner.token_budget import TokenBudget

def test_input_within_budget():
    budget = TokenBudget(max_input=10000, max_output=2000)
    text = "short evidence"
    result = budget.truncate_input(text)
    assert result == text

def test_input_exceeds_budget():
    budget = TokenBudget(max_input=100, max_output=2000)
    text = "x" * 500  # exceeds 100 * 4 = 400 chars
    result = budget.truncate_input(text)
    assert len(result) == 400


def test_token_usage_logged():
    budget = TokenBudget(max_input=10000, max_output=2000)
    budget.record_usage(incident_id="inc-1", input_tokens=500, output_tokens=300)
    usage = budget.get_usage("inc-1")
    assert usage["input_tokens"] == 500
    assert usage["output_tokens"] == 300


def test_total_cost_calculated():
    budget = TokenBudget(max_input=10000, max_output=2000)
    budget.record_usage("inc-1", input_tokens=1000, output_tokens=500)
    cost = budget.get_total_cost("inc-1")
    assert cost > 0

    