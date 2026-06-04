"""Unit tests for alert triggering functionality"""

import pytest
import time
from unittest.mock import patch, MagicMock
from collectors.base.base_collector import BaseCollector


# Create a concrete subclass for testing
class _TestCollector(BaseCollector):
    """Concrete collector for testing alert functionality"""
    
    def collect(self):
        return {"test": 42}


class TestAlertTrigger:
    """Test alert triggering functionality"""
    
    def test_alert_enabled(self):
        """Test alert when enabled"""
        collector = _TestCollector()
        collector.set_alert_config({"enabled": True, "type": "stdout"})
        
        # Alert should be triggered (printed to stdout)
        with patch('builtins.print') as mock_print:
            collector.alert("WARNING", "Test Title", "Test Message", "test_metric", 42)
            
            # Check that alert was printed
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("WARNING" in call and "Test Title" in call for call in calls)
    
    def test_alert_disabled(self):
        """Test alert when disabled"""
        collector = _TestCollector()
        collector.set_alert_config({"enabled": False})
        
        # Alert should NOT be triggered
        with patch('builtins.print') as mock_print:
            collector.alert("WARNING", "Test Title", "Test Message")
            
            # Alert message should not be printed
            calls = [str(call) for call in mock_print.call_args_list]
            assert not any("WARNING" in call and "Test Title" in call for call in calls)
    
    def test_alert_levels(self):
        """Test all alert levels"""
        collector = _TestCollector()
        collector.set_alert_config({"enabled": True, "type": "stdout"})
        
        with patch('builtins.print') as mock_print:
            for level in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
                collector._alert_history = {}  # Reset history
                collector.alert(level, f"{level} Title", f"{level} Message")
            
            # All levels should be printed
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("INFO" in call for call in calls)
            assert any("WARNING" in call for call in calls)
            assert any("ERROR" in call for call in calls)
            assert any("CRITICAL" in call for call in calls)
    
    def test_invalid_alert_level(self):
        """Test invalid alert level"""
        collector = _TestCollector()
        collector.set_alert_config({"enabled": True, "type": "stdout"})
        
        with patch('builtins.print') as mock_print:
            collector.alert("INVALID", "Test", "Message")
            
            # Should print error about invalid level
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Invalid alert level" in call for call in calls)
    
    def test_alert_cooldown(self):
        """Test alert cooldown mechanism"""
        collector = _TestCollector()
        collector.set_alert_config({"enabled": True, "type": "stdout"})
        collector._alert_cooldown = 1  # 1 second cooldown
        
        with patch('builtins.print') as mock_print:
            # First alert should go through
            collector.alert("WARNING", "Test", "Message", "test_metric", 42)
            
            # Second alert within cooldown should be blocked
            collector.alert("WARNING", "Test", "Message", "test_metric", 42)
            
            # Wait for cooldown to expire
            time.sleep(1.1)
            
            # Third alert should go through after cooldown
            collector.alert("WARNING", "Test", "Message", "test_metric", 42)
        
        # Count WARNING messages
        calls = [str(call) for call in mock_print.call_args_list]
        warning_calls = [call for call in calls if "WARNING" in call and "Test" in call]
        
        # Should have 2 warnings (first and third), not 3
        assert len(warning_calls) == 2
    
    def test_alert_cooldown_different_metrics(self):
        """Test cooldown is metric-specific"""
        collector = _TestCollector()
        collector.set_alert_config({"enabled": True, "type": "stdout"})
        collector._alert_cooldown = 1  # 1 second cooldown
        
        with patch('builtins.print') as mock_print:
            # Alert for metric1
            collector.alert("WARNING", "Test", "Message", "metric1", 42)
            
            # Alert for metric2 should NOT be blocked by metric1's cooldown
            collector.alert("WARNING", "Test", "Message", "metric2", 42)
        
        # Both alerts should go through
        calls = [str(call) for call in mock_print.call_args_list]
        warning_calls = [call for call in calls if "WARNING" in call and "Test" in call]
        
        assert len(warning_calls) == 2
    
    def test_webhook_alert(self):
        """Test webhook alert sending"""
        collector = _TestCollector()
        collector.set_alert_config({
            "enabled": True,
            "type": "webhook",
            "webhook_url": "https://example.com/webhook",
            "target": "test@example.com"
        })
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            collector.alert("ERROR", "Test Alert", "Test Message", "test_metric", 42)
            
            # Verify webhook was called
            assert mock_urlopen.called
            args = mock_urlopen.call_args[0][0]
            assert args.full_url == "https://example.com/webhook"
    
    def test_webhook_alert_failure(self):
        """Test webhook alert failure handling"""
        collector = _TestCollector()
        collector.set_alert_config({
            "enabled": True,
            "type": "webhook",
            "webhook_url": "https://example.com/webhook"
        })
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = Exception("Connection failed")
            
            with patch('builtins.print') as mock_print:
                collector.alert("ERROR", "Test Alert", "Test Message")
                
                # Should print error message
                calls = [str(call) for call in mock_print.call_args_list]
                assert any("Failed to send webhook" in call for call in calls)
    
    def test_webhook_url_not_configured(self):
        """Test webhook without URL"""
        collector = _TestCollector()
        collector.set_alert_config({
            "enabled": True,
            "type": "webhook"
        })
        
        with patch('builtins.print') as mock_print:
            collector.alert("ERROR", "Test Alert", "Test Message")
            
            # Should print error about missing URL
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Webhook URL not configured" in call for call in calls)
    
    def test_alert_without_metric_name(self):
        """Test alert without metric name (no cooldown)"""
        collector = _TestCollector()
        collector.set_alert_config({"enabled": True, "type": "stdout"})
        collector._alert_cooldown = 1
        
        with patch('builtins.print') as mock_print:
            # Multiple alerts without metric name should all go through
            collector.alert("WARNING", "Test", "Message")
            collector.alert("WARNING", "Test", "Message")
            collector.alert("WARNING", "Test", "Message")
        
        # All 3 alerts should be printed
        calls = [str(call) for call in mock_print.call_args_list]
        warning_calls = [call for call in calls if "WARNING" in call and "Test" in call]
        
        assert len(warning_calls) == 3
    
    def test_alert_payload_structure(self):
        """Test alert payload structure for webhook"""
        collector = _TestCollector()
        collector.set_alert_config({
            "enabled": True,
            "type": "webhook",
            "webhook_url": "https://example.com/webhook",
            "target": "admin@example.com"
        })
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            collector.alert("CRITICAL", "Critical Alert", "System down", "cpu", 100)
            
            # Verify the request data
            request = mock_urlopen.call_args[0][0]
            data = request.data.decode('utf-8')
            payload = json.loads(data)
            
            assert payload["level"] == "CRITICAL"
            assert payload["title"] == "Critical Alert"
            assert payload["message"] == "System down"
            assert payload["collector"] == "_TestCollector"
            assert payload["metric_name"] == "cpu"
            assert payload["metric_value"] == 100
            assert payload["target"] == "admin@example.com"
            assert "timestamp" in payload


import json  # Needed for test_alert_payload_structure
