"""Unit tests for LocalStorageCollector (SystemStatsCollector)"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from collectors.local_storage import SystemStatsCollector, HAS_PSUTIL


class TestLocalStorageCollector:
    """Test SystemStatsCollector functionality"""
    
    def test_collector_initialization(self):
        """Test collector initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = SystemStatsCollector(
                host="127.0.0.1",
                port=12345,
                interval=5,
                storage_path=tmpdir
            )
            
            assert collector.host == "127.0.0.1"
            assert collector.port == 12345
            assert collector.interval == 5
            assert collector._storage_path == tmpdir
    
    def test_collect_with_psutil(self):
        """Test collect with psutil available"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = SystemStatsCollector(storage_path=tmpdir)
            result = collector.collect()
            
            assert "cpu_percent" in result
            assert "mem_percent" in result
            assert "mem_total_mb" in result
            assert "mem_used_mb" in result
            assert "status" not in result  # No warning when psutil is available
    
    def test_collect_without_psutil(self):
        """Test collect when psutil is not available"""
        with patch.dict('sys.modules', {'psutil': None}):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Reimport to test fallback
                import importlib
                from collectors import local_storage
                importlib.reload(local_storage)
                
                collector = local_storage.SystemStatsCollector(storage_path=tmpdir)
                result = collector.collect()
                
                # Should have default values and status warning
                assert result["cpu_percent"] == 0.0
                assert result["mem_percent"] == 0.0
                assert result["mem_total_mb"] == 0.0
                assert result["mem_used_mb"] == 0.0
                assert "status" in result
                assert "System stats unavailable" in result["status"]
    
    def test_storage_directory_created(self):
        """Test that storage directory is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "data")
            collector = SystemStatsCollector(storage_path=storage_path)
            
            assert os.path.exists(storage_path)
    
    def test_metrics_to_lines(self):
        """Test metrics conversion to protocol lines"""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = SystemStatsCollector(storage_path=tmpdir)
            
            metrics = {
                "cpu_percent": 42.5,
                "mem_percent": 65.2,
                "mem_total_mb": 16384.0,
                "mem_used_mb": 10485.76
            }
            
            lines = collector.metrics_to_lines(metrics)
            
            assert len(lines) == 4
            assert any("T|cpu_percent" in line for line in lines)
            assert any("T|mem_percent" in line for line in lines)
            assert any("T|mem_total_mb" in line for line in lines)
            assert any("T|mem_used_mb" in line for line in lines)
    
    def test_on_success_callback(self):
        """Test success callback"""
        if not HAS_PSUTIL:
            pytest.skip("psutil not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = SystemStatsCollector(storage_path=tmpdir)
            metrics = {"cpu_percent": 42.5, "mem_percent": 65.2}
            
            # Should not raise any exception
            collector._on_success(metrics)
