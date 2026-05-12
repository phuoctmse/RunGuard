import pytest

from reasoner.processor import Processor


def test_process_evidence_job():
    p = Processor()
    job = {"type": "collect_evidence", "payload": {"pod": "api-server-xyz", "namespace": "production"}}
    result = p.process(job)
    assert result["status"] == "completed"
    assert "api-server-xyz" in result["message"]


def test_process_unknown_job():
    p = Processor()
    job = {"type": "unknown"}
    with pytest.raises(ValueError, match="unknown job type"):
        p.process(job)