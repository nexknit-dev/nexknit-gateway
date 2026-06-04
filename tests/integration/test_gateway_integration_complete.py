"""Complete integration tests for Gateway module"""

import pytest
import asyncio
import json
import time
from unittest.mock import patch, MagicMock

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


class TestGatewayIntegration:
    """Test Gateway integration scenarios"""

    def test_payload_aggregation_and_serialization(self):
        """Test end-to-end payload aggregation and serialization"""
        items = [
            {"type": "Trend", "name": "cpu", "content": 42.5, "time": get_ts()},
            {"type": "Trend", "name": "cpu", "content": 45.0, "time": get_ts()},
            {"type": "Status", "name": "status", "content": "running", "time": get_ts()},
            {"type": "Index", "name": "temp", "content": 25.0, "time": get_ts()},
        ]
        
        # Aggregate items
        batches = aggregate(items)
        
        # Create payload
        payload = make_payload("TestNode", batches)
        
        # Verify payload structure
        assert payload["n"] == "TestNode"
        assert "t" in payload
        assert "p" in payload
        assert "Trend" in payload["p"]
        assert "Status" in payload["p"]
        assert "Index" in payload["p"]
        
        # Verify JSON serialization
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        assert parsed["n"] == "TestNode"

    def test_message_parsing_chain(self):
        """Test message parsing chain from raw string to aggregated data"""
        raw_messages = [
            "Trend|cpu|42.5",
            "Status|service|running",
            "Index|memory|65.2",
            "Trend|cpu|48.0",
        ]
        
        parsed_items = []
        for msg in raw_messages:
            parsed = parse_message(msg)
            parsed_items.append(parsed)
        
        # Aggregate all parsed items
        batches = aggregate(parsed_items)
        
        assert len(batches["Trend"]["cpu"]) == 2
        assert batches["Status"]["service"][0][1] == "running"
        assert batches["Index"]["memory"][0][1] == 65.2

    def test_http_post_with_real_payload(self):
        """Test HTTP POST with a realistic payload structure"""
        batches = {
            "Trend": {
                "cpu": [[get_ts(), 42.5], [get_ts(), 45.0]],
                "memory": [[get_ts(), 65.2]]
            },
            "Status": {
                "service": [[get_ts(), "running"]]
            }
        }
        payload = make_payload("TestNode", batches)
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            http_post("https://example.com/api/push", "test_key", payload)
            
            # Verify the call was made
            mock_urlopen.assert_called_once()

    def test_send_async_integration(self):
        """Test async send integration"""
        batches = {
            "Trend": {
                "cpu": [[get_ts(), 42.5]]
            }
        }
        payload = make_payload("TestNode", batches)
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            # Run async function synchronously
            asyncio.run(send_async("https://example.com/api/push", "test_key", payload, 5.0))
            
            mock_urlopen.assert_called_once()

    def test_parse_message_edge_cases(self):
        """Test parsing edge cases"""
        # Empty message
        result = parse_message("")
        assert result["type"] == "Log"
        
        # Missing content
        result = parse_message("Trend|cpu")
        assert result["type"] == "Log"
        
        # Invalid float value
        result = parse_message("Index|temp|not_a_number")
        assert result["type"] == "Log"

    def test_aggregate_with_large_data(self):
        """Test aggregation with multiple data points"""
        items = []
        base_time = get_ts()
        
        for i in range(10):
            items.append({"type": "Trend", "name": "cpu", "content": 40.0 + i, "time": base_time + i})
        
        batches = aggregate(items)
        
        assert len(batches["Trend"]["cpu"]) == 10
        assert batches["Trend"]["cpu"][0][1] == 40.0
        assert batches["Trend"]["cpu"][-1][1] == 49.0

    def test_payload_timestamp_consistency(self):
        """Test payload timestamp consistency"""
        payload1 = make_payload("Node1", {})
        time.sleep(0.1)
        payload2 = make_payload("Node2", {})
        
        # Timestamps should be different
        assert payload1["t"] != payload2["t"]
        
        # Both should be valid timestamps
        assert payload1["t"] > 0
        assert payload2["t"] > 0
