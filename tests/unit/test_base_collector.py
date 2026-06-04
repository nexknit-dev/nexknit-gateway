"""Unit tests for BaseCollector"""

import pytest
from collectors.base.base_collector import BaseCollector


# Create a concrete subclass for testing (prefixed with _ to avoid pytest collection)
class _TestCollector(BaseCollector):
    """Concrete collector for testing BaseCollector functionality"""
    
    def collect(self):
        return {"test": 42}


class TestBaseCollector:
    """Test BaseCollector functionality"""
    
    def test_protocol_types(self):
        """Test PROTOCOL_TYPES dictionary"""
        assert "I" in BaseCollector.PROTOCOL_TYPES
        assert "Index" in BaseCollector.PROTOCOL_TYPES
        assert "T" in BaseCollector.PROTOCOL_TYPES
        assert "Trend" in BaseCollector.PROTOCOL_TYPES
        assert "L" in BaseCollector.PROTOCOL_TYPES
        assert "Log" in BaseCollector.PROTOCOL_TYPES
        assert "S" in BaseCollector.PROTOCOL_TYPES
        assert "Status" in BaseCollector.PROTOCOL_TYPES
    
    def test_alert_levels(self):
        """Test ALERT_LEVELS list"""
        assert "INFO" in BaseCollector.ALERT_LEVELS
        assert "WARNING" in BaseCollector.ALERT_LEVELS
        assert "ERROR" in BaseCollector.ALERT_LEVELS
        assert "CRITICAL" in BaseCollector.ALERT_LEVELS
    
    def test_parse_message_valid(self):
        """Test parse_message with valid input"""
        collector = _TestCollector()
        
        # Test Index type
        result = collector.parse_message("I|cpu|42.5")
        assert result["type"] == "Index"
        assert result["name"] == "cpu"
        assert result["content"] == 42.5
        
        # Test Trend type
        result = collector.parse_message("T|memory|65.2")
        assert result["type"] == "Trend"
        assert result["name"] == "memory"
        assert result["content"] == 65.2
        
        # Test Status type
        result = collector.parse_message("S|status|running")
        assert result["type"] == "Status"
        assert result["name"] == "status"
        assert result["content"] == "running"
        
        # Test Log type
        result = collector.parse_message("L|error|something went wrong")
        assert result["type"] == "Log"
        assert result["name"] == "error"
        assert result["content"] == "something went wrong"
    
    def test_parse_message_invalid(self):
        """Test parse_message with invalid input"""
        collector = _TestCollector()
        
        # Missing parts
        result = collector.parse_message("invalid")
        assert result["type"] == "Log"
        assert result["name"] == "WrongLog"
        
        # Empty name
        result = collector.parse_message("T||42")
        assert result["type"] == "Log"
        assert result["name"] == "WrongLog"
        
        # Invalid number format
        result = collector.parse_message("I|cpu|not_a_number")
        assert result["type"] == "Log"
        assert result["name"] == "WrongLog"
    
    def test_format_metric(self):
        """Test format_metric method"""
        collector = _TestCollector()
        
        result = collector.format_metric("T", "cpu", 42.5)
        assert result == "T|cpu|42.5"
        
        result = collector.format_metric("S", "status", "running")
        assert result == "S|status|running"
    
    def test_metrics_to_lines(self):
        """Test metrics_to_lines method"""
        collector = _TestCollector()
        
        metrics = {
            "cpu_percent": 42.5,
            "memory_percent": 65.2,
            "status": "running"
        }
        
        lines = collector.metrics_to_lines(metrics)
        
        assert len(lines) == 3
        assert any("T|cpu_percent|42.5" in line for line in lines)
        assert any("T|memory_percent|65.2" in line for line in lines)
        assert any("S|status|running" in line for line in lines)
    
    def test_alert_cooldown(self):
        """Test alert cooldown mechanism"""
        collector = _TestCollector(host="127.0.0.1", port=12345)
        collector._alert_config = {"enabled": True, "type": "stdout"}
        collector._alert_cooldown = 1  # 1 second cooldown
        
        # First alert should go through
        collector.alert("WARNING", "Test", "Message", "test_metric", 42)
        
        # Second alert within cooldown should be blocked
        import time
        collector.alert("WARNING", "Test", "Message", "test_metric", 42)
        
        # After cooldown, alert should go through
        time.sleep(1.1)
        collector.alert("WARNING", "Test", "Message", "test_metric", 42)
    
    def test_alert_disabled(self):
        """Test alert when disabled"""
        collector = _TestCollector(host="127.0.0.1", port=12345)
        collector._alert_config = {"enabled": False}
        
        # Alert should not be sent when disabled
        collector.alert("WARNING", "Test", "Message")
