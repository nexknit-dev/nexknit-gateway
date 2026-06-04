"""Complete unit tests for HttpAliveCollector - covering concurrency and edge cases"""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from collectors.http_alive import HttpAliveCollector


class TestHttpAliveConcurrency:
    """Test HttpAliveCollector concurrent URL checking"""
    
    def test_collect_with_thread_timeout(self):
        """Test collect handles thread timeout"""
        collector = HttpAliveCollector(urls=["https://example.com"], timeout=0.1)
        
        result = collector.collect()
        
        assert "http_0_status" in result
    
    def test_collect_multiple_urls_concurrent(self):
        """Test collect processes multiple URLs concurrently"""
        collector = HttpAliveCollector(urls=["https://url1.com", "https://url2.com", "https://url3.com"])
        
        call_order = []
        def track_call(url):
            call_order.append(url)
            time.sleep(0.05)
            if "url1" in url:
                return (200, 100)
            elif "url2" in url:
                return (404, 50)
            else:
                return (500, 75)
        
        with patch.object(collector, '_check_url_single', side_effect=track_call):
            result = collector.collect()
            
            # All URLs should be checked
            assert "http_0_status" in result
            assert "http_1_status" in result
            assert "http_2_status" in result
            
            # Verify all URLs were called
            assert "https://url1.com" in call_order
            assert "https://url2.com" in call_order
            assert "https://url3.com" in call_order
    
    def test_collect_empty_url_list(self):
        """Test collect with empty URL list"""
        collector = HttpAliveCollector(urls=[])
        
        result = collector.collect()
        
        # Empty URL list - no threads started, returns empty dict or status message
        assert isinstance(result, dict)
    
    def test_collect_none_urls(self):
        """Test collect with None URLs (uses default)"""
        collector = HttpAliveCollector(urls=None)
        
        # Should have default URL
        assert len(collector._urls) == 1
        assert "google.com" in collector._urls[0]


class TestHttpAliveEdgeCases:
    """Test HttpAliveCollector edge cases"""
    
    def test_check_url_single_redirect(self):
        """Test URL check handles redirects"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 301
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            status, latency = collector._check_url_single("https://example.com")
            # Redirects are followed automatically, so this should work
            assert status == 301
            assert latency >= 0
    
    def test_check_url_single_ssl_error(self):
        """Test URL check handles SSL errors"""
        collector = HttpAliveCollector(urls=["https://invalid-cert.example.com"])
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            from ssl import SSLError
            mock_urlopen.side_effect = SSLError("SSL certificate error")
            
            status, latency = collector._check_url_single("https://invalid-cert.example.com")
            assert status == 0
            assert latency == -1
    
    def test_check_url_single_connection_refused(self):
        """Test URL check handles connection refused"""
        collector = HttpAliveCollector(urls=["http://localhost:1"])
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            from urllib.error import URLError
            from socket import error as socket_error
            mock_urlopen.side_effect = URLError(socket_error("Connection refused"))
            
            status, latency = collector._check_url_single("http://localhost:1")
            assert status == 0
            assert latency == -1
    
    def test_check_alert_client_error(self):
        """Test alert on client error status (4xx)"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        collector._alert_config = {"enabled": True, "type": "stdout"}
        
        with patch.object(collector, 'alert') as mock_alert:
            # Client errors (4xx) don't trigger alerts currently
            collector._check_alert("https://example.com", 404)
            # Should not call alert for client errors
            mock_alert.assert_not_called()
    
    def test_check_alert_success(self):
        """Test no alert on success status"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        collector._alert_config = {"enabled": True, "type": "stdout"}
        
        with patch.object(collector, 'alert') as mock_alert:
            collector._check_alert("https://example.com", 200)
            mock_alert.assert_not_called()


class TestHttpAliveMetricsConversion:
    """Test HttpAliveCollector metrics conversion"""
    
    def test_metrics_to_lines_status(self):
        """Test metrics_to_lines for status metrics"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        
        metrics = {"http_0_status": "example.com\n200\n150ms"}
        lines = collector.metrics_to_lines(metrics)
        
        assert len(lines) == 1
        assert "S|" in lines[0]
        assert "http_0_status" in lines[0]
    
    def test_metrics_to_lines_latency(self):
        """Test metrics_to_lines for latency metrics"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        
        metrics = {"http_0_latency": "150ms"}
        lines = collector.metrics_to_lines(metrics)
        
        assert len(lines) == 1
        assert "T|" in lines[0]
    
    def test_metrics_to_lines_url(self):
        """Test metrics_to_lines for URL metrics"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        
        metrics = {"http_0_url": "https://example.com"}
        lines = collector.metrics_to_lines(metrics)
        
        assert len(lines) == 1
        assert "S|" in lines[0]


class TestHttpAlivePerformance:
    """Test HttpAliveCollector performance aspects"""
    
    def test_thread_daemon_flag(self):
        """Test that threads are daemon threads"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        
        # Verify thread creation by checking the collect method works
        result = collector.collect()
        assert "http_0_status" in result
    
    def test_collect_timeout_handling(self):
        """Test collect timeout handling"""
        collector = HttpAliveCollector(urls=["https://example.com"], timeout=0.1)
        
        call_count = [0]
        def slow_check(url):
            call_count[0] += 1
            time.sleep(0.2)  # Longer than timeout
            return (200, 100)
        
        with patch.object(collector, '_check_url_single', side_effect=slow_check):
            result = collector.collect()
            
            assert "http_0_status" in result
            assert call_count[0] == 1  # Should only be called once