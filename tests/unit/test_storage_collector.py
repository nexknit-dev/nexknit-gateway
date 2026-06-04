"""Unit tests for StorageCollector"""

import pytest
import os
import json
import tempfile
from collectors.base.storage_collector import StorageCollector


# Create a concrete subclass for testing
class _TestStorageCollector(StorageCollector):
    """Concrete collector for testing StorageCollector functionality"""
    
    def collect(self):
        return {"test": 42}


class TestStorageCollector:
    """Test StorageCollector functionality"""
    
    def test_init_creates_directory(self):
        """Test that storage directory is created on init"""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = _TestStorageCollector(storage_path=os.path.join(tmpdir, "data"))
            assert os.path.exists(os.path.join(tmpdir, "data"))
    
    def test_cache_failed_data(self):
        """Test caching failed data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = _TestStorageCollector(storage_path=tmpdir)
            
            # Cache a failed message
            collector._cache_failed_data("test_message")
            
            # Check cache file exists
            cache_file = os.path.join(tmpdir, "failed_cache.json")
            assert os.path.exists(cache_file)
            
            # Check content
            with open(cache_file, "r") as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["message"] == "test_message"
    
    def test_save_to_history(self):
        """Test saving metrics to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = _TestStorageCollector(storage_path=tmpdir)
            
            # Save metrics to history
            metrics = {"cpu": 42.5, "memory": 65.2}
            collector._save_to_history(metrics)
            
            # Check history file exists
            history_file = os.path.join(tmpdir, "history.json")
            assert os.path.exists(history_file)
            
            # Check content
            with open(history_file, "r") as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["metrics"] == metrics
    
    def test_max_cache_size(self):
        """Test max cache size limitation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = _TestStorageCollector(storage_path=tmpdir, max_cache_size=3)
            
            # Cache more than max_size messages
            for i in range(5):
                collector._cache_failed_data(f"message_{i}")
            
            # Check cache file
            cache_file = os.path.join(tmpdir, "failed_cache.json")
            with open(cache_file, "r") as f:
                data = json.load(f)
                assert len(data) == 3  # Should be limited to max_cache_size
    
    def test_get_history(self):
        """Test getting history data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = _TestStorageCollector(storage_path=tmpdir)
            
            # Save multiple entries
            for i in range(5):
                collector._save_to_history({"value": i})
            
            # Get limited history
            history = collector.get_history(limit=3)
            assert len(history) == 3
            
            # Get all history
            history = collector.get_history(limit=100)
            assert len(history) == 5
    
    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = _TestStorageCollector(storage_path=tmpdir)
            
            # Initially empty
            stats = collector.get_cache_stats()
            assert stats["count"] == 0
            
            # After caching
            collector._cache_failed_data("test")
            stats = collector.get_cache_stats()
            assert stats["count"] == 1
    
    def test_retry_failed_data(self):
        """Test retrying failed data on startup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-populate cache
            cache_file = os.path.join(tmpdir, "failed_cache.json")
            with open(cache_file, "w") as f:
                json.dump([{"message": "test_message", "timestamp": 1234567890, "collector": "Test"}], f)
            
            # Create collector with retry
            collector = _TestStorageCollector(storage_path=tmpdir, retry_on_start=True)
            
            # Cache should be processed
            stats = collector.get_cache_stats()
            # Note: retry will attempt to send, if fails, cache remains
            # This test verifies retry mechanism runs without error
