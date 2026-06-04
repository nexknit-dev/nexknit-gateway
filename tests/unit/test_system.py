"""Unit tests for SystemCollector"""

import pytest
from unittest.mock import patch, MagicMock
from collectors.system import SystemCollector, HAS_PSUTIL


class TestSystemCollector:
    """Test SystemCollector functionality"""
    
    def test_collector_initialization(self):
        """Test collector initialization"""
        collector = SystemCollector(host="127.0.0.1", port=12345, interval=5)
        
        assert collector.host == "127.0.0.1"
        assert collector.port == 12345
        assert collector.interval == 5
        assert collector.cpu is not None
        assert collector.memory is not None
        assert collector.disk is not None
        assert collector.network is not None
    
    def test_collect_with_psutil(self):
        """Test collect with psutil available"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        collector = SystemCollector()
        result = collector.collect()
        
        assert "cpu_percent" in result
        assert "memory_percent" in result
        assert "disk_percent" in result
        assert "hostname" in result
        assert "platform" in result
    
    def test_collect_without_psutil(self):
        """Test collect when psutil is not available"""
        with patch.dict('sys.modules', {'psutil': None}):
            # Force reimport to test fallback
            import importlib
            from collectors import system
            importlib.reload(system)
            
            collector = SystemCollector()
            result = collector.collect()
            
            # Should have status warning
            assert "status" in result
            assert "Metrics may be simulated" in result["status"]
    
    def test_collect_metrics_range(self):
        """Test that collected metrics are in valid range"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        collector = SystemCollector()
        result = collector.collect()
        
        # CPU percent should be between 0 and 100
        assert 0 <= result["cpu_percent"] <= 100
        
        # Memory percent should be between 0 and 100
        assert 0 <= result["memory_percent"] <= 100
        
        # Disk percent should be between 0 and 100
        assert 0 <= result["disk_percent"] <= 100
    
    def test_hostname_and_platform(self):
        """Test hostname and platform info"""
        collector = SystemCollector()
        result = collector.collect()
        
        assert isinstance(result["hostname"], str)
        assert len(result["hostname"]) > 0
        assert isinstance(result["platform"], str)
        assert len(result["platform"]) > 0
    
    def test_network_metrics(self):
        """Test network metrics"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        collector = SystemCollector()
        result = collector.collect()
        
        assert "network_sent" in result
        assert "network_recv" in result
        assert result["network_sent"] >= 0
        assert result["network_recv"] >= 0
    
    def test_uptime(self):
        """Test uptime metrics"""
        collector = SystemCollector()
        result = collector.collect()
        
        assert "uptime_seconds" in result
        assert result["uptime_seconds"] >= 0
        assert isinstance(result["uptime_seconds"], int)
