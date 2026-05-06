"""Tests for UI page helpers."""

from unittest.mock import MagicMock, patch

import pytest

from runguard.ui.pages import _api_get, _api_post, _api_url


@patch("runguard.ui.pages.st")
def test_api_url_default(mock_st):
    mock_st.session_state = {}
    assert _api_url() == "http://localhost:8000"


@patch("runguard.ui.pages.st")
def test_api_url_custom(mock_st):
    mock_st.session_state = {"api_url": "http://custom:9000"}
    assert _api_url() == "http://custom:9000"


@patch("runguard.ui.pages.httpx")
@patch("runguard.ui.pages.st")
def test_api_get_success(mock_st, mock_httpx):
    mock_st.session_state = {}
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "ok"}
    mock_response.raise_for_status = MagicMock()
    mock_httpx.get.return_value = mock_response
    result = _api_get("/health")
    assert result == {"status": "ok"}


@patch("runguard.ui.pages.httpx")
@patch("runguard.ui.pages.st")
def test_api_get_error(mock_st, mock_httpx):
    mock_st.session_state = {}
    mock_httpx.get.side_effect = Exception("connection refused")
    result = _api_get("/health")
    assert result == {}
    mock_st.error.assert_called_once()


@patch("runguard.ui.pages.httpx")
@patch("runguard.ui.pages.st")
def test_api_post_success(mock_st, mock_httpx):
    mock_st.session_state = {}
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "inc-001"}
    mock_response.raise_for_status = MagicMock()
    mock_httpx.post.return_value = mock_response
    result = _api_post("/incidents", {"source": "manual"})
    assert result == {"id": "inc-001"}


@patch("runguard.ui.pages.httpx")
@patch("runguard.ui.pages.st")
def test_api_post_error(mock_st, mock_httpx):
    mock_st.session_state = {}
    mock_httpx.post.side_effect = Exception("timeout")
    result = _api_post("/incidents")
    assert result == {}
    mock_st.error.assert_called_once()


@patch("runguard.ui.pages.httpx")
@patch("runguard.ui.pages.st")
def test_api_post_no_data(mock_st, mock_httpx):
    mock_st.session_state = {}
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status = MagicMock()
    mock_httpx.post.return_value = mock_response
    result = _api_post("/incidents")
    mock_httpx.post.assert_called_once_with(
        "http://localhost:8000/incidents", json={}, timeout=10.0
    )
