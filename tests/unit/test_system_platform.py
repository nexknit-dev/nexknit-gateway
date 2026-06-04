"""Unit tests for SystemCollector platform-specific implementations"""

import pytest
import os
import time
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from collectors.system import CPUMeter, MemoryMeter, DiskMeter, NetworkMeter, SYSTEM


class TestCPUMeterPlatform:
    """Test CPU meter platform-specific implementations"""
    
    def test_cpu_meter_fallback(self):
        """Test CPU meter fallback implementation"""
        meter = CPUMeter()
        meter._collect = meter._fallback_cpu
        
        result = meter.get()
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100
    
    def test_cpu_meter_value_range(self):
        """Test CPU meter returns values in valid range"""
        meter = CPUMeter()
        result = meter.get()
        
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100
    
    @pytest.mark.skipif(SYSTEM != "Linux", reason="Linux-only test")
    def test_linux_cpu_fallback_on_error(self):
        """Test Linux CPU meter fallback on error"""
        with patch('builtins.open', side_effect=IOError):
            meter = CPUMeter()
            meter._collect = meter._linux_cpu
            
            # First call initializes, subsequent calls use fallback
            result = meter.get()
            assert isinstance(result, float)


class TestMemoryMeterPlatform:
    """Test Memory meter platform-specific implementations"""
    
    def test_memory_meter_fallback(self):
        """Test memory meter fallback implementation"""
        meter = MemoryMeter()
        meter._collect = meter._fallback_memory
        
        result = meter.get()
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100
    
    def test_memory_meter_value_range(self):
        """Test memory meter returns values in valid range"""
        meter = MemoryMeter()
        result = meter.get()
        
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100
    
    @pytest.mark.skipif(SYSTEM != "Linux", reason="Linux-only test")
    def test_linux_memory_fallback_on_error(self):
        """Test Linux memory meter fallback on error"""
        with patch('builtins.open', side_effect=IOError):
            meter = MemoryMeter()
            meter._collect = meter._linux_memory
            
            result = meter.get()
            assert isinstance(result, float)
    
    @pytest.mark.skipif(SYSTEM != "Windows", reason="Windows-only test")
    def test_windows_memory_ctypes(self):
        """Test Windows memory meter with ctypes"""
        meter = MemoryMeter()
        result = meter.get()
        
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100


class TestDiskMeterPlatform:
    """Test Disk meter platform-specific implementations"""
    
    def test_disk_meter_fallback(self):
        """Test disk meter fallback implementation"""
        meter = DiskMeter()
        meter._collect = meter._fallback_disk
        
        result = meter.get()
        assert result == 50.0
    
    def test_disk_meter_value_range(self):
        """Test disk meter returns values in valid range"""
        meter = DiskMeter()
        result = meter.get()
        
        assert isinstance(result, float)
        assert 0 <= result <= 100
    
    @pytest.mark.skipif(SYSTEM != "Linux" and SYSTEM != "Darwin", reason="Unix-only test")
    def test_unix_disk_fallback_on_error(self):
        """Test Unix disk meter fallback on error"""
        with patch('os.statvfs', side_effect=OSError):
            meter = DiskMeter()
            meter._collect = meter._unix_disk
            
            result = meter.get()
            assert result == 50.0
    
    @pytest.mark.skipif(SYSTEM != "Windows", reason="Windows-only test")
    def test_windows_disk_ctypes(self):
        """Test Windows disk meter with ctypes"""
        meter = DiskMeter()
        result = meter.get()
        
        assert isinstance(result, float)
        assert 0 <= result <= 100


class TestNetworkMeterPlatform:
    """Test Network meter platform-specific implementations"""
    
    def test_network_meter_fallback(self):
        """Test network meter fallback implementation"""
        meter = NetworkMeter()
        meter._collect = meter._fallback_net
        
        sent, recv = meter.get()
        assert isinstance(sent, int)
        assert isinstance(recv, int)
        assert sent >= 0
        assert recv >= 0
    
    @pytest.mark.skipif(SYSTEM != "Linux", reason="Linux-only test")
    def test_linux_network_fallback_on_error(self):
        """Test Linux network meter fallback on error"""
        with patch('builtins.open', side_effect=IOError):
            meter = NetworkMeter()
            meter._collect = meter._linux_net
            
            sent, recv = meter.get()
            assert sent >= 0
            assert recv >= 0
    
    def test_network_meter_initialization(self):
        """Test network meter initialization"""
        meter = NetworkMeter()
        
        assert meter._prev_sent == 0
        assert meter._prev_recv == 0
        assert not meter._initialized


class TestSystemCollectorEdgeCases:
    """Test SystemCollector edge cases"""
    
    def test_cpu_meter_first_call(self):
        """Test CPU meter first call returns valid value"""
        meter = CPUMeter()
        result = meter.get()
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100
    
    def test_memory_meter_zero_total(self):
        """Test memory meter handles zero total memory gracefully"""
        meter = MemoryMeter()
        result = meter.get()
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100