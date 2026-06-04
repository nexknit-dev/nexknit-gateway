"""Unit tests for HttpAliveCollector"""

import pytest
from unittest.mock import patch, MagicMock
from collectors.http_alive import HttpAliveCollector


class TestHttpAliveCollector:
    """Test HttpAliveCollector functionality"""
    
    def test_extract_domain(self):
        """Test domain extraction"""
        collector = HttpAliveCollector(urls=["https://www.google.com"])
        
        assert collector._extract_domain("https://www.google.com") == "google.com"
        assert collector._extract_domain("https://api.example.com/v1/users") == "api.example.com"
        assert collector._extract_domain("http://localhost:8080") == "localhost:8080"
        assert collector._extract_domain("https://github.com/nexknit-dev/nexknit-gateway") == "github.com"
    
    def test_check_url_single_success(self):
        """Test successful URL check"""
        collector = HttpAliveCollector(urls=["https://www.google.com"])
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            
            status, latency = collector._check_url_single("https://www.google.com")
            assert status == 200
            assert latency >= 0
    
    def test_check_url_single_failure(self):
        """Test failed URL check"""
        collector = HttpAliveCollector(urls=["https://invalid.example.invalid"])
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Connection error")
            
            status, latency = collector._check_url_single("https://invalid.example.invalid")
            assert status == 0
            assert latency == -1
    
    def test_check_url_single_timeout(self):
        """Test URL check timeout"""
        collector = HttpAliveCollector(urls=["https://slow.example.com"], timeout=1)
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = TimeoutError("Timed out")
            
            status, latency = collector._check_url_single("https://slow.example.com")
            assert status == 0
            assert latency == -1
    
    def test_collect_single_url(self):
        """Test collecting single URL"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        
        with patch.object(collector, '_check_url_single') as mock_check:
            mock_check.return_value = (200, 150)
            
            result = collector.collect()
            assert "http_0_status" in result
            assert "example.com" in result["http_0_status"]
            assert "200" in result["http_0_status"]
    
    def test_collect_multiple_urls(self):
        """Test collecting multiple URLs"""
        collector = HttpAliveCollector(urls=["https://example.com", "https://google.com"])
        
        with patch.object(collector, '_check_url_single') as mock_check:
            mock_check.side_effect = [(200, 150), (404, 100)]
            
            result = collector.collect()
            assert "http_0_status" in result
            assert "http_1_status" in result
            assert "example.com" in result["http_0_status"]
            assert "google.com" in result["http_1_status"]
    
    def test_collect_with_network_error(self):
        """Test collecting when network is unavailable"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        
        with patch.object(collector, '_check_url_single') as mock_check:
            mock_check.return_value = (0, -1)
            
            result = collector.collect()
            assert "http_0_status" in result
            assert "Network Error" in result["http_0_status"]
    
    def test_check_alert_error(self):
        """Test alert on error status"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        collector._alert_config = {"enabled": True, "type": "stdout"}
        
        with patch.object(collector, 'alert') as mock_alert:
            collector._check_alert("https://example.com", 0)
            mock_alert.assert_called_once_with(
                level="ERROR",
                title="HTTP Service Unavailable",
                message="URL https://example.com is unreachable",
                metric_name="http_https://example.com",
                metric_value="DOWN"
            )
    
    def test_check_alert_server_error(self):
        """Test alert on server error status"""
        collector = HttpAliveCollector(urls=["https://example.com"])
        collector._alert_config = {"enabled": True, "type": "stdout"}
        
        with patch.object(collector, 'alert') as mock_alert:
            collector._check_alert("https://example.com", 500)
            mock_alert.assert_called_once_with(
                level="WARNING",
                title="HTTP Server Error",
                message="URL https://example.com returned status code 500",
                metric_name="http_https://example.com",
                metric_value=500
            )
