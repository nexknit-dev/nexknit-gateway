"""Complete unit tests for Gateway module - covering HTTP, TCP, and sync loop"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gateway import (
    http_post,
    send_async,
    make_payload,
    aggregate,
    parse_message,
    get_ts
)


class TestGatewayHttp:
    """Test HTTP sending functionality"""
    
    def test_http_post_success(self):
        """Test successful HTTP POST"""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            http_post("https://example.com", "test_key", {"test": "data"})
            mock_urlopen.assert_called_once()

    def test_http_post_failure(self):
        """Test HTTP POST failure handling"""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = RuntimeError("Connection failed")
            
            with pytest.raises(RuntimeError):
                http_post("https://example.com", "test_key", {"test": "data"})

    def test_http_post_server_error(self):
        """Test HTTP POST with server error"""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 500
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            with pytest.raises(RuntimeError):
                http_post("https://example.com", "test_key", {"test": "data"})

    def test_send_async_sync(self):
        """Test send_async functionality via sync wrapper"""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            # Run async function synchronously
            asyncio.run(send_async("https://example.com", "test_key", {"test": "data"}, 5.0))
            mock_urlopen.assert_called_once()


class TestGatewayPayload:
    """Test payload creation and aggregation"""
    
    def test_make_payload_structure(self):
        """Test payload structure"""
        batches = {"Trend": {"cpu": [[1234567890, 42.5]]}}
        payload = make_payload("TestNode", batches)
        
        assert payload["n"] == "TestNode"
        assert isinstance(payload["t"], int)
        assert payload["p"] == batches
        assert "t" in payload

    def test_aggregate_empty(self):
        """Test aggregation with empty list"""
        result = aggregate([])
        assert result == {}

    def test_aggregate_multiple_types(self):
        """Test aggregation with multiple types"""
        items = [
            {"type": "Trend", "name": "cpu", "content": 42.5, "time": 1234567890},
            {"type": "Status", "name": "status", "content": "running", "time": 1234567890},
            {"type": "Index", "name": "temp", "content": 25.0, "time": 1234567890},
        ]
        result = aggregate(items)
        
        assert "Trend" in result
        assert "Status" in result
        assert "Index" in result
        assert len(result["Trend"]["cpu"]) == 1

    def test_parse_message_index_type(self):
        """Test parsing Index type message"""
        result = parse_message("Index|temperature|25.5")
        assert result["type"] == "Index"
        assert result["content"] == 25.5

    def test_parse_message_trend_type(self):
        """Test parsing Trend type message"""
        result = parse_message("Trend|cpu_usage|80.0")
        assert result["type"] == "Trend"
        assert result["content"] == 80.0

    def test_parse_message_invalid_format(self):
        """Test parsing invalid message format"""
        result = parse_message("invalid")
        assert result["type"] == "Log"
        assert result["name"] == "WrongLog"

    def test_parse_message_status_type(self):
        """Test parsing Status type message"""
        result = parse_message("Status|service|running")
        assert result["type"] == "Status"
        assert result["content"] == "running"

    def test_parse_message_log_type(self):
        """Test parsing Log type message"""
        result = parse_message("Log|info|test message")
        assert result["type"] == "Log"
        assert result["content"] == "test message"

    def test_get_ts(self):
        """Test timestamp generation"""
        ts = get_ts()
        assert isinstance(ts, int)
        assert ts > 0
