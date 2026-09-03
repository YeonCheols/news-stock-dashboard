import pytest

from src.collectors import retry


def test_retries_transient_failure_with_exponential_backoff(monkeypatch):
    attempts = []
    delays = []
    monkeypatch.setattr(retry, "DATA_REQUEST_MAX_RETRIES", 2)
    monkeypatch.setattr(retry, "DATA_REQUEST_RETRY_DELAY_SECONDS", 0.5)
    monkeypatch.setattr(retry.time, "sleep", delays.append)

    def operation():
        attempts.append(1)
        if len(attempts) < 3:
            raise TimeoutError("temporary timeout")
        return "success"

    assert retry.run_with_retries(operation) == "success"
    assert len(attempts) == 3
    assert delays == [0.5, 1.0]


def test_reraises_final_failure_without_extra_sleep(monkeypatch):
    delays = []
    monkeypatch.setattr(retry, "DATA_REQUEST_MAX_RETRIES", 1)
    monkeypatch.setattr(retry, "DATA_REQUEST_RETRY_DELAY_SECONDS", 1)
    monkeypatch.setattr(retry.time, "sleep", delays.append)

    with pytest.raises(TimeoutError, match="timeout"):
        retry.run_with_retries(lambda: (_ for _ in ()).throw(TimeoutError("timeout")))

    assert delays == [1]
