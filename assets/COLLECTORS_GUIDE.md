# Nexknit Collectors Guide

This guide provides instructions on how to use the example collectors included in the Nexknit Gateway project.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Collector Types](#collector-types)
   - [System Collector](#system-collector)
   - [HTTP Alive Collector](#http-alive-collector)
   - [GPU Collector](#gpu-collector)
   - [Local Storage Collector](#local-storage-collector)
4. [Running Collectors](#running-collectors)
   - [Running Standalone](#running-standalone)
   - [Running via Gateway](#running-via-gateway)
5. [How to Reference Example Collectors](#how-to-reference-example-collectors)
6. [Advanced Development](#advanced-development)
   - [Custom Collector Development](#custom-collector-development)
   - [Extending Base Classes](#extending-base-classes)
   - [Best Practices](#best-practices)
7. [Configuration](#configuration)
8. [Metric Types](#metric-types)
9. [Output Modes](#output-modes)

## Overview

Nexknit Gateway includes several example collectors that demonstrate how to collect different types of system metrics. These collectors can be run standalone or through the centralized gateway.

## Prerequisites

- Python 3.8+
- Required packages: `psutil` (for enhanced system metrics)
- NVIDIA GPU tools (`nvidia-smi`) for GPU collector

Install dependencies:
```bash
pip install psutil
```

## Collector Types

<details>
<summary><strong>System Collector</strong></summary>

**File:** `collectors/system.py`

Collects comprehensive system metrics including:
- CPU usage percentage
- Memory usage percentage
- Disk usage percentage
- Network I/O (bytes sent/received)
- System load average
- CPU temperature (Linux only)
- System uptime
- Hostname and OS information

**Key Features:**
- Cross-platform support (Linux, macOS, Windows)
- Fallback mode when `psutil` is not available (returns simulated data)
- Real-time metric collection
- Automatic warning when dependencies are missing

**Environment Requirements:**
- **Optional**: `psutil` library for accurate metrics
- If `psutil` is not installed, collector returns simulated values and displays warning

**Warning Behavior:**
- **Console**: `[WARN] psutil library not installed. System metrics may be inaccurate.`
- **Frontend**: Adds `status` field with warning message: `⚠️ Metrics may be simulated - Install psutil for accurate data`

**Usage Example:**
```bash
python collectors/system.py --host 127.0.0.1 --port 12345 --interval 5
```

**Installation:**
```bash
pip install psutil
```

</details>

<details>
<summary><strong>HTTP Alive Collector</strong></summary>

**File:** `collectors/http_alive.py`

Monitors the availability of HTTP endpoints:
- Checks URL status codes
- Measures response latency
- Extracts main domain from URLs
- Returns individual status for each URL

**Key Features:**
- Network status monitoring
- Domain extraction for cleaner output
- Per-URL status reporting
- Automatic warning when network is unavailable

**Environment Requirements:**
- Network connection to target URLs
- No external dependencies required

**Warning Behavior:**
- **Console**: `[WARN] HTTP Alive Collector: Cannot reach {url} - network may be unavailable`
- **Frontend**: Returns status message: `{domain}\n⚠️ Network Error\nCheck your network connection`

**Usage Example:**
```bash
python collectors/http_alive.py --host 127.0.0.1 --port 12345 --urls https://example.com https://google.com
```

</details>

<details>
<summary><strong>GPU Collector</strong></summary>

**File:** `collectors/gpu.py`

Monitors NVIDIA GPU status:
- Memory usage (used/total)
- GPU utilization percentage
- GPU temperature
- Running process detection with change logging

**Key Features:**
- Automatic NVIDIA GPU detection
- Process change monitoring with cooldown
- Per-GPU status reporting
- Automatic warning when NVIDIA GPU is unavailable

**Environment Requirements:**
- NVIDIA GPU hardware
- `nvidia-smi` tool installed (usually comes with NVIDIA drivers)

**Warning Behavior:**
- **Console**: `[WARN] NVIDIA GPU not detected. Please install NVIDIA drivers and nvidia-smi tool.`
- **Frontend**: Returns status message: `⚠️ GPU Unavailable - Please install NVIDIA drivers and nvidia-smi`

**Usage Example:**
```bash
python collectors/gpu.py --host 127.0.0.1 --port 12345 --interval 5 --process-log-interval 60
```

**Installation:**
- Install NVIDIA drivers for your GPU
- `nvidia-smi` is typically included with NVIDIA drivers

</details>

<details>
<summary><strong>Local Storage Collector</strong></summary>

**File:** `collectors/local_storage.py`

Collects system stats with local storage capability:
- CPU and memory usage
- Automatic data persistence
- Failed data caching
- Historical metric tracking

**Key Features:**
- Inherits from `StorageCollector`
- Automatic retry on startup
- Data backup and recovery

**Usage Example:**
```bash
python collectors/local_storage.py --host 127.0.0.1 --port 12345 --storage-path ./data
```

</details>

## Running Collectors

### Running Standalone

Each collector can be run independently:

```bash
# System Collector
python collectors/system.py --host 127.0.0.1 --port 12345 --interval 5

# HTTP Alive Collector
python collectors/http_alive.py --host 127.0.0.1 --port 12345 --urls https://example.com https://google.com

# GPU Collector
python collectors/gpu.py --host 127.0.0.1 --port 12345 --interval 5

# Local Storage Collector
python collectors/local_storage.py --host 127.0.0.1 --port 12345 --storage-path ./data
```

### Running via Gateway

Use `run_gateway.py` to start the gateway with all collectors:

```bash
# Start gateway with default settings
python run_gateway.py

# Start gateway on a specific port
python run_gateway.py --port 12345
```

## How to Reference Example Collectors

You can reference and use the example collectors in your own projects in several ways:

### Importing Collectors

```python
# Import individual collectors
from collectors.system import SystemCollector
from collectors.http_alive import HttpAliveCollector
from collectors.gpu import GPUCollector
from collectors.local_storage import SystemStatsCollector

# Create instances
system_collector = SystemCollector(host="127.0.0.1", port=12345, interval=5)
http_collector = HttpAliveCollector(urls=["https://example.com"])
```

### Using Collectors as Modules

```python
# Run collector programmatically
collector = SystemCollector()
metrics = collector.collect()
print(metrics)

# Access base functionality
collector.send_tcp_message("Hello from collector")
collector.alert("WARNING", "High CPU", "CPU usage exceeded 90%")
```

### Extending Existing Collectors

```python
from collectors.system import SystemCollector

class CustomSystemCollector(SystemCollector):
    def collect(self):
        # Call parent method
        metrics = super().collect()
        # Add custom metrics
        metrics["custom_field"] = "custom_value"
        return metrics
```

## Advanced Development

<details>
<summary><strong>Custom Collector Development</strong></summary>

### Step-by-Step Guide

To create a custom collector:

1. **Create a new file** in `collectors/` directory
2. **Import base classes** from `collectors.base`
3. **Inherit** from `BaseCollector` or `StorageCollector`
4. **Implement** the `collect()` method
5. **Optionally override** `metrics_to_lines()` for custom formatting

### Example: Simple Collector

```python
from collectors.base import BaseCollector
from typing import Dict, Any

class MyCollector(BaseCollector):
    """Custom collector template"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 12345, interval: int = 5):
        super().__init__(host, port, interval)
        # Initialize custom attributes
        self._custom_config = {}
    
    def collect(self) -> Dict[str, Any]:
        """Collect custom metrics"""
        return {
            "custom_metric": 42,
            "status": "running"
        }
    
    def metrics_to_lines(self, metrics: Dict[str, Any]) -> list:
        """Convert metrics to protocol lines"""
        lines = []
        lines.append(self.format_metric("T", "custom_metric", metrics["custom_metric"]))
        lines.append(self.format_metric("S", "status", metrics["status"]))
        return lines
```

### Adding CLI Support

```python
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="My Custom Collector")
    parser.add_argument("--host", default="127.0.0.1", help="Gateway address")
    parser.add_argument("--port", type=int, default=12345, help="Gateway port")
    parser.add_argument("--interval", type=int, default=5, help="Collection interval")
    args = parser.parse_args()
    
    collector = MyCollector(host=args.host, port=args.port, interval=args.interval)
    collector.run()

if __name__ == "__main__":
    main()
```

</details>

<details>
<summary><strong>Extending Base Classes</strong></summary>

### BaseCollector Features

The `BaseCollector` class provides:
- TCP connection management
- Metric formatting
- Alert system
- Error handling
- Configurable output modes

### StorageCollector Features

The `StorageCollector` class extends `BaseCollector` with:
- Local file storage
- Data persistence
- Failed message caching
- History tracking

### Example: Using Storage Features

```python
from collectors.base import StorageCollector

class MyStorageCollector(StorageCollector):
    def collect(self):
        # Your collection logic here
        data = {"value": 100}
        
        # Save to history
        self._save_to_history(data)
        
        # Cache failed data (if needed)
        # self._cache_failed_data("error message")
        
        return data
```

### Overriding Base Methods

```python
from collectors.base import BaseCollector

class AdvancedCollector(BaseCollector):
    def _on_success(self, metrics):
        """Custom success callback"""
        print(f"Successfully collected: {len(metrics)} metrics")
    
    def _on_failure(self, error):
        """Custom failure callback"""
        print(f"Collection failed: {error}")
        # Send alert
        self.alert("ERROR", "Collection Failed", str(error))
```

</details>

<details>
<summary><strong>Best Practices</strong></summary>

### Code Organization

1. **Single Responsibility**: Each collector should focus on one type of metric collection
2. **Error Handling**: Always handle exceptions gracefully
3. **Logging**: Use appropriate logging for debugging
4. **Configuration**: Make configurable parameters explicit
5. **Testing**: Write unit tests for custom collectors

### Performance Considerations

1. **Avoid Blocking Calls**: Use async operations for I/O bound tasks
2. **Batch Processing**: Group related operations
3. **Resource Management**: Release resources properly
4. **Interval Control**: Use appropriate collection intervals

### Security Practices

1. **Input Validation**: Validate all inputs
2. **Secure Communication**: Use HTTPS for external calls
3. **Secrets Management**: Don't hardcode sensitive data
4. **Least Privilege**: Run collectors with minimal permissions

### Testing Guidelines

```python
import unittest
from collectors.my_collector import MyCollector

class TestMyCollector(unittest.TestCase):
    def test_collect(self):
        collector = MyCollector()
        metrics = collector.collect()
        self.assertIn("custom_metric", metrics)
        self.assertEqual(metrics["status"], "running")

if __name__ == "__main__":
    unittest.main()
```

</details>

## Alert System Guide

### Overview

The `BaseCollector` class provides a complete alert system. Subclasses can directly call `self.alert()` to send alerts. Key features:

- **Four Alert Levels**: INFO, WARNING, ERROR, CRITICAL
- **Cooldown Mechanism**: Auto-cooldown for duplicate alerts
- **Multiple Outputs**: stdout and webhook notifications
- **Auto Deduplication**: Based on alert level and metric name

### Alert Configuration

Alerts can be configured in `run_gateway.py`:

```python
ALERT_CONFIG = {
    "enabled": True,                    # Enable/disable alerts
    "type": "stdout",                   # "stdout" or "webhook"
    "target": "admin@example.com",      # Alert recipient identifier
    "webhook_url": "",                  # Webhook URL for external notifications
}
```

### Alert Method Signature

```python
def alert(
    self,
    level: str,           # Alert level: INFO, WARNING, ERROR, CRITICAL
    title: str,           # Alert title
    message: str,         # Alert message content
    metric_name: str = None,   # Associated metric name (for deduplication)
    metric_value: Any = None   # Associated metric value
)
```

### Sending Alerts in Subclasses

Here's a complete example of using alerts in a custom collector:

```python
from collectors.base import BaseCollector
from typing import Dict, Any

class MyCollector(BaseCollector):
    """Custom collector demonstrating alert functionality"""
    
    def __init__(self, host="127.0.0.1", port=12345, interval=5):
        super().__init__(host, port, interval)
        # Configure alerts (usually done by run_gateway.py)
        self.set_alert_config({
            "enabled": True,
            "type": "stdout",
            "target": "admin@example.com"
        })
    
    def collect(self) -> Dict[str, Any]:
        # Simulate data collection
        cpu_usage = 95.5  # Simulate high CPU usage
        
        # Detect anomalies and send alerts
        if cpu_usage > 90:
            self.alert(
                level="WARNING",
                title="High CPU Usage",
                message=f"CPU usage is {cpu_usage}%, which exceeds the threshold of 90%",
                metric_name="cpu_percent",
                metric_value=cpu_usage
            )
        
        # Critical anomaly
        if cpu_usage > 95:
            self.alert(
                level="CRITICAL",
                title="Critical CPU Alert",
                message=f"CPU usage critical: {cpu_usage}%",
                metric_name="cpu_percent",
                metric_value=cpu_usage
            )
        
        return {"cpu_percent": cpu_usage}
```

### Alert Cooldown Mechanism

The base class has a built-in cooldown mechanism, default 300 seconds (5 minutes):

```python
# In base class implementation
self._alert_cooldown = 300  # Cooldown time in seconds

# Auto-check cooldown status when alerting
if time.time() - last_alert < self._alert_cooldown:
    print(f"[ALERT] Alert cooldown active for {key}")
    return  # Skip sending
```

### Custom Alert Cooldown

```python
class MyCollector(BaseCollector):
    def __init__(self, host="127.0.0.1", port=12345, interval=5):
        super().__init__(host, port, interval)
        # Set custom cooldown time (1 minute)
        self._alert_cooldown = 60
```

### Webhook Alert Configuration

Configure webhook for alert notifications:

```python
ALERT_CONFIG = {
    "enabled": True,
    "type": "webhook",
    "target": "ops-team",
    "webhook_url": "https://your-alert-service.com/webhook"
}
```

Webhook payload format:
```json
{
    "level": "WARNING",
    "title": "High CPU Usage",
    "message": "CPU usage is 95%",
    "collector": "MyCollector",
    "metric_name": "cpu_percent",
    "metric_value": 95.5,
    "timestamp": "2024-01-01T12:00:00",
    "target": "admin@example.com"
}
```

### Complete Example: Collector with Alerts

```python
from collectors.base import BaseCollector
import psutil

class SmartMonitorCollector(BaseCollector):
    """Smart monitoring collector with alert functionality"""
    
    CPU_WARNING_THRESHOLD = 80
    CPU_CRITICAL_THRESHOLD = 95
    MEM_WARNING_THRESHOLD = 85
    MEM_CRITICAL_THRESHOLD = 95
    
    def collect(self):
        metrics = {}
        
        # Collect CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics["cpu_percent"] = cpu_percent
        
        # CPU alert logic
        if cpu_percent >= self.CPU_CRITICAL_THRESHOLD:
            self.alert(
                "CRITICAL",
                "CPU Critical",
                f"CPU usage at {cpu_percent}% - system may be unresponsive",
                "cpu_percent",
                cpu_percent
            )
        elif cpu_percent >= self.CPU_WARNING_THRESHOLD:
            self.alert(
                "WARNING",
                "CPU Warning",
                f"CPU usage at {cpu_percent}% - consider scaling",
                "cpu_percent",
                cpu_percent
            )
        
        # Collect memory usage
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        metrics["mem_percent"] = mem_percent
        
        # Memory alert logic
        if mem_percent >= self.MEM_CRITICAL_THRESHOLD:
            self.alert(
                "CRITICAL",
                "Memory Critical",
                f"Memory usage at {mem_percent}% - system may crash",
                "mem_percent",
                mem_percent
            )
        elif mem_percent >= self.MEM_WARNING_THRESHOLD:
            self.alert(
                "WARNING",
                "Memory Warning",
                f"Memory usage at {mem_percent}%",
                "mem_percent",
                mem_percent
            )
        
        return metrics
    
    def _on_failure(self, attempt):
        """Auto-alert when sending fails"""
        super()._on_failure(attempt)
        if attempt >= self._max_failures:
            self.alert(
                "ERROR",
                "Collector Failed",
                f"Failed to send metrics after {attempt} attempts",
                "collector_status",
                "failed"
            )
```

### Alert Level Reference

| Level | Purpose | Example Scenarios |
|-------|---------|-------------------|
| **INFO** | Informational notifications | Service startup, configuration changes |
| **WARNING** | Warning level | Metric threshold exceeded, performance degradation |
| **ERROR** | Error level | Collection failure, connection errors |
| **CRITICAL** | Critical level | System crash, resource exhaustion |

## Configuration

### Collector Options

| Collector | Options | Description |
|-----------|---------|-------------|
| System | `--host`, `--port`, `--interval` | Gateway host, port, collection interval |
| HTTP Alive | `--urls` | List of URLs to monitor |
| GPU | `--process-log-interval` | Interval for process change logging |
| Local Storage | `--storage-path` | Path for local data storage |

## Metric Types

| Type | Code | Description |
|------|------|-------------|
| Status | `S` | String status information |
| Trend | `T` | Numeric value for trend tracking |
| Info | `I` | Informational metric |
| Log | `L` | Log message |

## Output Modes

- **TCP Mode**: Send metrics to gateway via TCP
- **Stdout Mode**: Print metrics to console (for debugging)

```bash
python collectors/system.py --output stdout
```