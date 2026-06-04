"""Integration tests for gateway"""

import pytest
import time
import subprocess
import sys
import os


class TestGatewayIntegration:
    """Test gateway integration scenarios"""
    
    def test_collector_imports(self):
        """Test that all collectors can be imported"""
        # Test imports for all collectors
        from collectors import http_alive
        from collectors import gpu
        from collectors import system
        from collectors import local_storage
        from collectors.base import base_collector
        from collectors.base import storage_collector
        
        # Verify key classes exist
        assert hasattr(http_alive, "HttpAliveCollector")
        assert hasattr(gpu, "GPUCollector")
        assert hasattr(system, "SystemCollector")
        assert hasattr(local_storage, "SystemStatsCollector")
        assert hasattr(base_collector, "BaseCollector")
        assert hasattr(storage_collector, "StorageCollector")
    
    def test_collector_inheritance(self):
        """Test collector inheritance hierarchy"""
        from collectors.base.base_collector import BaseCollector
        from collectors.base.storage_collector import StorageCollector
        from collectors.http_alive import HttpAliveCollector
        from collectors.gpu import GPUCollector
        from collectors.system import SystemCollector
        from collectors.local_storage import SystemStatsCollector
        
        # Check inheritance
        assert issubclass(StorageCollector, BaseCollector)
        assert issubclass(HttpAliveCollector, BaseCollector)
        assert issubclass(GPUCollector, BaseCollector)
        assert issubclass(SystemCollector, BaseCollector)
        assert issubclass(SystemStatsCollector, StorageCollector)
    
    def test_run_gateway_config(self):
        """Test run_gateway.py configuration"""
        # This test verifies that run_gateway.py can be imported
        import importlib
        run_gateway = importlib.import_module("run_gateway")
        
        # Verify the module loads correctly
        assert hasattr(run_gateway, "main")
        assert hasattr(run_gateway, "ALERT_CONFIG")
        assert hasattr(run_gateway, "COLLECTORS")
        
        # Verify ALERT_CONFIG structure
        assert "enabled" in run_gateway.ALERT_CONFIG
        assert "type" in run_gateway.ALERT_CONFIG
        
        # Verify COLLECTORS structure
        assert isinstance(run_gateway.COLLECTORS, list)
        assert len(run_gateway.COLLECTORS) > 0
    
    def test_gateway_module_import(self):
        """Test that gateway module can be imported"""
        import importlib
        gateway = importlib.import_module("gateway")
        
        # Verify main function exists
        assert hasattr(gateway, "main")
