"""Integration tests for collectors"""

import pytest
import time
import threading
from collectors.http_alive import HttpAliveCollector
from collectors.system import SystemCollector
from collectors.base.base_collector import BaseCollector


# Create a concrete subclass for testing
class _TestCollector(BaseCollector):
    """Concrete collector for testing"""
    def collect(self):
        return {"test": 42}


class TestCollectorIntegration:
    """Test collector integration scenarios"""
    
    def test_http_collector_multiple_urls(self):
        """Test HTTP collector with multiple URLs"""
        urls = ["https://example.com", "https://httpbin.org/status/200", "https://httpbin.org/status/404"]
        collector = HttpAliveCollector(urls=urls, interval=1)
        
        result = collector.collect()
        
        # Should have status for each URL
        assert "http_0_status" in result
        assert "http_1_status" in result
        assert "http_2_status" in result
        
        # Should have domain names
        assert "example.com" in result["http_0_status"]
        assert "httpbin.org" in result["http_1_status"]
        assert "httpbin.org" in result["http_2_status"]
    
    def test_collector_metrics_format(self):
        """Test that collectors produce properly formatted metrics"""
        collector = SystemCollector(interval=1)
        result = collector.collect()
        
        # Convert to protocol lines
        lines = collector.metrics_to_lines(result)
        
        # Each line should follow the protocol format
        for line in lines:
            parts = line.split("|")
            assert len(parts) == 3, f"Invalid format: {line}"
            assert parts[0] in ["I", "T", "L", "S"], f"Invalid type: {parts[0]}"
            assert len(parts[1]) > 0, f"Empty name: {line}"
    
    def test_collector_concurrent_execution(self):
        """Test multiple collectors running concurrently"""
        results = []
        
        def run_collector(collector, collector_name):
            result = collector.collect()
            results.append((collector_name, result))
        
        collectors = [
            ("system", SystemCollector(interval=1)),
            ("http", HttpAliveCollector(urls=["https://example.com"], interval=1))
        ]
        
        # Run collectors concurrently
        threads = []
        for name, collector in collectors:
            thread = threading.Thread(target=run_collector, args=(collector, name))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
        
        # Both collectors should have produced results
        assert len(results) == 2
        
        # Check that we got results from both types
        system_result = None
        http_result = None
        for name, result in results:
            if name == "system":
                system_result = result
            else:
                http_result = result
        
        assert system_result is not None, "System collector should have produced results"
        assert http_result is not None, "HTTP collector should have produced results"
        assert "cpu_percent" in system_result or "status" in system_result
        assert "http_0_status" in http_result
    
    def test_alert_config_propagation(self):
        """Test alert configuration propagation to collectors"""
        alert_config = {
            "enabled": True,
            "type": "stdout",
            "target": "test@example.com"
        }
        
        collector = HttpAliveCollector(urls=["https://example.com"])
        collector.set_alert_config(alert_config)
        
        assert collector._alert_config["enabled"] is True
        assert collector._alert_config["type"] == "stdout"
        assert collector._alert_config["target"] == "test@example.com"
    
    def test_collector_error_handling(self):
        """Test collector error handling"""
        # Test with invalid URL
        collector = HttpAliveCollector(urls=["https://invalid-url-12345.invalid"])
        result = collector.collect()
        
        # Should handle error gracefully
        assert "http_0_status" in result
        assert "Network Error" in result["http_0_status"]
    
    def test_collector_timeout(self):
        """Test collector timeout handling"""
        collector = HttpAliveCollector(
            urls=["https://httpbin.org/delay/10"],
            timeout=1  # Short timeout
        )
        
        start = time.time()
        result = collector.collect()
        elapsed = time.time() - start
        
        # Should complete within timeout + margin
        assert elapsed < 5  # Should timeout quickly
        assert "http_0_status" in result
    
    def test_base_collector_tcp_send(self, mock_server):
        """Test TCP message sending"""
        collector = _TestCollector()
        collector.host = mock_server["host"]
        collector.port = mock_server["port"]
        
        # Send a test message
        success = collector.send_tcp_message("T|test|42.5\n")
        
        # Wait for message to be received
        time.sleep(0.1)
        
        assert success is True
        assert len(mock_server["messages"]) == 1
        assert mock_server["messages"][0] == "T|test|42.5"
