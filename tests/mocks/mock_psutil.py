"""Mock psutil module for testing system metrics"""

from unittest.mock import MagicMock, patch


class MockVirtualMemory:
    """Mock virtual memory info"""
    
    def __init__(self, total=16 * 1024**3, available=8 * 1024**3, percent=50.0):
        self.total = total
        self.available = available
        self.percent = percent
        self.used = total - available
        self.free = available


class MockDiskUsage:
    """Mock disk usage info"""
    
    def __init__(self, total=500 * 1024**3, used=200 * 1024**3):
        self.total = total
        self.used = used
        self.free = total - used
        self.percent = (used / total) * 100


class MockNetIOCounters:
    """Mock network I/O counters"""
    
    def __init__(self, bytes_sent=1000000, bytes_recv=2000000):
        self.bytes_sent = bytes_sent
        self.bytes_recv = bytes_recv


class MockCPUStats:
    """Mock CPU stats"""
    
    def __init__(self):
        self.ctx_switches = 1000000
        self.interrupts = 500000
        self.soft_interrupts = 100000
        self.syscalls = 2000000


class MockPsutilModule:
    """Mock psutil module for testing"""
    
    def __init__(self):
        self._cpu_percent = 42.5
        self._virtual_memory = MockVirtualMemory()
        self._disk_usage = MockDiskUsage()
        self._net_io_counters = MockNetIOCounters()
        self._cpu_stats = MockCPUStats()
        self._cpu_count = 8
        self._boot_time = 1600000000.0
    
    def cpu_percent(self, interval=None):
        return self._cpu_percent
    
    def virtual_memory(self):
        return self._virtual_memory
    
    def disk_usage(self, path):
        return self._disk_usage
    
    def net_io_counters(self, pernic=False):
        if pernic:
            return {"eth0": self._net_io_counters}
        return self._net_io_counters
    
    def cpu_stats(self):
        return self._cpu_stats
    
    def cpu_count(self, logical=True):
        return self._cpu_count
    
    def boot_time(self):
        return self._boot_time
    
    def process_iter(self):
        return iter([])
    
    def Process(self, pid):
        mock_proc = MagicMock()
        mock_proc.name.return_value = f"process_{pid}"
        mock_proc.pid = pid
        mock_proc.memory_info.return_value = MagicMock(rss=100 * 1024**2)
        mock_proc.cpu_percent.return_value = 10.0
        return mock_proc
    
    def set_cpu_percent(self, value):
        """Set mock CPU percent"""
        self._cpu_percent = value
    
    def set_memory_percent(self, value):
        """Set mock memory percent"""
        total = self._virtual_memory.total
        used = (value / 100) * total
        self._virtual_memory = MockVirtualMemory(
            total=total,
            available=total - used,
            percent=value
        )
    
    def reset(self):
        """Reset to default values"""
        self.__init__()


def patch_psutil():
    """Create a patch for psutil module"""
    mock_module = MockPsutilModule()
    patcher = patch("psutil", mock_module)
    return patcher, mock_module


# Predefined system metrics for testing
SYSTEM_METRICS = {
    "normal": {
        "cpu_percent": 42.5,
        "memory_percent": 65.2,
        "disk_percent": 45.0,
        "network_sent": 1000000,
        "network_recv": 2000000,
    },
    "high_load": {
        "cpu_percent": 95.0,
        "memory_percent": 90.0,
        "disk_percent": 85.0,
        "network_sent": 10000000,
        "network_recv": 20000000,
    },
    "low_load": {
        "cpu_percent": 5.0,
        "memory_percent": 20.0,
        "disk_percent": 10.0,
        "network_sent": 10000,
        "network_recv": 20000,
    }
}
