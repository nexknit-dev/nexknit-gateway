"""Unit tests for Gateway module"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

# Import gateway functions
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from gateway import (
    load_config,
    parse_message,
    aggregate,
    make_payload,
    get_ts
)


class TestGatewayConfig:
    """Test gateway configuration handling"""
    
    def test_load_config_default(self):
        """Test loading default config when file doesn't exist"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            os.remove(temp_path)  # Ensure file doesn't exist
            config, is_first_start = load_config(temp_path)
            
            assert is_first_start is True
            assert "gateway" in config
            assert "tcp_server" in config
            assert "cloudflare" in config
            assert config["gateway"]["node_name"] == "Nexknit_Dev"
            assert config["tcp_server"]["port"] == 12345
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_load_config_existing(self):
        """Test loading existing config file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({
                "gateway": {"node_name": "TestNode"},
                "tcp_server": {"port": 54321},
                "cloudflare": {"worker_url": "https://example.com"}
            }, f)
            temp_path = f.name
        
        try:
            config, is_first_start = load_config(temp_path)
            
            assert is_first_start is False
            assert config["gateway"]["node_name"] == "TestNode"
            assert config["tcp_server"]["port"] == 54321
            assert config["cloudflare"]["worker_url"] == "https://example.com"
        finally:
            os.remove(temp_path)
    
    def test_load_config_cli_overrides(self):
        """Test command line overrides"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({
                "cloudflare": {"worker_url": "https://old.com", "api_key": "old_key"}
            }, f)
            temp_path = f.name
        
        try:
            config, _ = load_config(temp_path, url="https://new.com", api_key="new_key")
            
            assert config["cloudflare"]["worker_url"] == "https://new.com"
            assert config["cloudflare"]["api_key"] == "new_key"
        finally:
            os.remove(temp_path)
    
    def test_load_config_url_trailing_slash(self):
        """Test URL trailing slash removal"""
        config, _ = load_config(url="https://example.com/")
        assert config["cloudflare"]["worker_url"] == "https://example.com"


class TestGatewayProtocol:
    """Test gateway protocol parsing"""
    
    def test_parse_message_valid(self):
        """Test parsing valid messages"""
        # Test Index type
        result = parse_message("I|cpu|42.5")
        assert result["type"] == "Index"
        assert result["name"] == "cpu"
        assert result["content"] == 42.5
        assert "time" in result
        
        # Test Trend type
        result = parse_message("T|memory|65.2")
        assert result["type"] == "Trend"
        assert result["name"] == "memory"
        assert result["content"] == 65.2
        
        # Test Status type
        result = parse_message("S|status|running")
        assert result["type"] == "Status"
        assert result["name"] == "status"
        assert result["content"] == "running"
        
        # Test Log type
        result = parse_message("L|error|something went wrong")
        assert result["type"] == "Log"
        assert result["name"] == "error"
        assert result["content"] == "something went wrong"
    
    def test_parse_message_invalid(self):
        """Test parsing invalid messages"""
        # Missing parts
        result = parse_message("invalid")
        assert result["type"] == "Log"
        assert result["name"] == "WrongLog"
        
        # Empty name
        result = parse_message("T||42")
        assert result["type"] == "Log"
        assert result["name"] == "WrongLog"
        
        # Invalid number format
        result = parse_message("I|cpu|not_a_number")
        assert result["type"] == "Log"
        assert result["name"] == "WrongLog"


class TestGatewayAggregation:
    """Test data aggregation functionality"""
    
    def test_aggregate_empty(self):
        """Test aggregation with empty list"""
        result = aggregate([])
        assert result == {}
    
    def test_aggregate_single_item(self):
        """Test aggregation with single item"""
        items = [{"type": "Trend", "name": "cpu", "content": 42.5, "time": 1234567890}]
        result = aggregate(items)
        
        assert "Trend" in result
        assert "cpu" in result["Trend"]
        assert len(result["Trend"]["cpu"]) == 1
        assert result["Trend"]["cpu"][0] == [1234567890, 42.5]
    
    def test_aggregate_multiple_items(self):
        """Test aggregation with multiple items of same type and name"""
        items = [
            {"type": "Trend", "name": "cpu", "content": 42.5, "time": 1234567890},
            {"type": "Trend", "name": "cpu", "content": 50.0, "time": 1234567891},
            {"type": "Status", "name": "status", "content": "running", "time": 1234567890},
        ]
        result = aggregate(items)
        
        assert len(result["Trend"]["cpu"]) == 2
        assert len(result["Status"]["status"]) == 1
    
    def test_aggregate_different_types(self):
        """Test aggregation with different types"""
        items = [
            {"type": "Trend", "name": "cpu", "content": 42.5, "time": 1234567890},
            {"type": "Status", "name": "status", "content": "running", "time": 1234567890},
            {"type": "Log", "name": "error", "content": "test", "time": 1234567890},
        ]
        result = aggregate(items)
        
        assert "Trend" in result
        assert "Status" in result
        assert "Log" in result


class TestGatewayPayload:
    """Test payload creation"""
    
    def test_make_payload(self):
        """Test payload creation"""
        batches = {"Trend": {"cpu": [[1234567890, 42.5]]}}
        payload = make_payload("TestNode", batches)
        
        assert payload["n"] == "TestNode"
        assert "t" in payload
        assert payload["p"] == batches
        assert isinstance(payload["t"], int)


class TestGatewayUtils:
    """Test utility functions"""
    
    def test_get_ts(self):
        """Test timestamp generation"""
        ts = get_ts()
        assert isinstance(ts, int)
        # Timestamp should be within reasonable range
        assert ts > 1000000000000  # After year 2000
        assert ts < 3000000000000  # Before year 2095
