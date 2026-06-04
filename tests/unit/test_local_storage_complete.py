"""Complete unit tests for LocalStorageCollector"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from collectors.local_storage import SystemStatsCollector, HAS_PSUTIL


class TestLocalStorageCollector:
    """Test SystemStatsCollector functionality"""
    
    def test_collector_initialization_defaults(self):
        """Test collector initialization with defaults"""
        collector = SystemStatsCollector()
        
        assert collector._cpu_usage == 0.0
        assert collector._mem_usage == 0.0
        assert collector._warned_psutil == False
    
    def test_collector_initialization_with_custom_params(self):
        """Test collector initialization with custom parameters"""
        collector = SystemStatsCollector(
            host="192.168.1.1",
            port=54321,
            interval=10,
            storage_path="/custom/path"
        )
        
        assert collector.host == "192.168.1.1"
        assert collector.port == 54321
        assert collector.interval == 10
    
    def test_collect_with_psutil_success(self):
        """Test collect with psutil available and working"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        collector = SystemStatsCollector()
        result = collector.collect()
        
        assert "cpu_percent" in result
        assert "mem_percent" in result
        assert "mem_total_mb" in result
        assert "mem_used_mb" in result
        
        # Verify values are reasonable
        assert isinstance(result["cpu_percent"], (int, float))
        assert isinstance(result["mem_percent"], (int, float))
        assert result["mem_total_mb"] >= 0
        assert result["mem_used_mb"] >= 0
    
    def test_collect_with_psutil_exception(self):
        """Test collect handles psutil exceptions"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        collector = SystemStatsCollector()
        collector._warned_psutil = True  # Skip warning
        
        # Patch both psutil.cpu_percent and psutil.virtual_memory to trigger exception
        with patch('psutil.cpu_percent', side_effect=Exception("Test error")):
            result = collector.collect()
            
            assert "cpu_percent" in result
            assert "mem_percent" in result
            assert "status" in result
    
    def test_collect_without_psutil(self):
        """Test collect when psutil is not available"""
        with patch.dict('sys.modules', {'psutil': None}):
            # Force reimport to test fallback
            import importlib
            from collectors import local_storage
            importlib.reload(local_storage)
            
            collector = local_storage.SystemStatsCollector()
            result = collector.collect()
            
            assert "cpu_percent" in result
            assert result["cpu_percent"] == 0.0
            assert "mem_percent" in result
            assert result["mem_percent"] == 0.0
            assert "status" in result
            assert "psutil" in result["status"]
    
    def test_collect_memory_values(self):
        """Test memory values are calculated correctly"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        collector = SystemStatsCollector()
        result = collector.collect()
        
        # Memory used should be less than or equal to total
        assert result["mem_used_mb"] <= result["mem_total_mb"]
        
        # Percent should be calculated correctly (avoid division by zero)
        if result["mem_total_mb"] > 0:
            expected_percent = (result["mem_used_mb"] / result["mem_total_mb"]) * 100
            assert abs(result["mem_percent"] - expected_percent) < 5  # Allow small tolerance
    
    def test_on_success_callback(self):
        """Test _on_success callback"""
        collector = SystemStatsCollector()
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            metrics = {"cpu_percent": 42.5, "mem_percent": 65.0}
            collector._on_success(metrics)
            
            # Verify success message was printed
            assert mock_print.call_count >= 1
            call_args = mock_print.call_args[0][0]
            assert "CPU" in call_args
            assert "Mem" in call_args
    
    def test_on_success_callback_missing_metrics(self):
        """Test _on_success with missing metrics"""
        collector = SystemStatsCollector()
        
        with patch('builtins.print') as mock_print:
            metrics = {"status": "test"}
            collector._on_success(metrics)
            
            # Should not print when cpu_percent or mem_percent missing
            mock_print.assert_not_called()
    
    def test_warning_only_once(self):
        """Test psutil warning is only printed once"""
        with patch.dict('sys.modules', {'psutil': None}):
            import importlib
            from collectors import local_storage
            importlib.reload(local_storage)
            
            collector = local_storage.SystemStatsCollector()
            
            with patch('builtins.print') as mock_print:
                # First collect should print warning
                collector.collect()
                warning_count = mock_print.call_count
                
                # Subsequent collects should not print warning again
                collector.collect()
                collector.collect()
                
                assert mock_print.call_count == warning_count  # Warning only once
    
    def test_collect_values_range(self):
        """Test collected values are in valid range"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        collector = SystemStatsCollector()
        result = collector.collect()
        
        # CPU percent should be between 0 and 100
        assert 0 <= result["cpu_percent"] <= 100
        
        # Memory percent should be between 0 and 100
        assert 0 <= result["mem_percent"] <= 100