"""Tests for SSM document executor."""

import boto3
import pytest
from moto import mock_aws

from runguard.aws.ssm_executor import SSMExecutor


@pytest.fixture
def ssm_executor():
    with mock_aws():
        yield SSMExecutor(region_name="us-east-1")


def test_trigger_ssm_document(ssm_executor):
    result = ssm_executor.trigger_document(
        document_name="AWS-RunShellScript",
        targets=["i-1234567890abcdef0"],
        parameters={"commands": ["echo hello"]},
    )
    assert result["status"] == "success"
    assert "execution_id" in result
