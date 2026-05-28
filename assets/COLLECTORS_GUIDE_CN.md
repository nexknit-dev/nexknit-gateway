# Nexknit 采集器使用指南

本文档提供了 Nexknit Gateway 项目中示例采集器的使用说明。

## 目录

1. [概述](#概述)
2. [前置条件](#前置条件)
3. [采集器类型](#采集器类型)
   - [系统采集器](##系统采集器)
   - [HTTP 存活采集器](##http-存活采集器)
   - [GPU 采集器](##gpu-采集器)
   - [本地存储采集器](##本地存储采集器)
4. [运行采集器](##运行采集器)
   - [独立运行](##独立运行)
   - [通过网关运行](##通过网关运行)
5. [如何引用示例采集器](#如何引用示例采集器)
6. [高级开发](#高级开发)
   - [自定义采集器开发](##自定义采集器开发)
   - [扩展基类](##扩展基类)
   - [最佳实践](##最佳实践)
7. [配置](#配置)
8. [指标类型](##指标类型)
9. [输出模式](##输出模式)

## 概述

Nexknit Gateway 包含多个示例采集器，展示如何收集不同类型的系统指标。这些采集器可以独立运行或通过集中网关运行。

## 前置条件

- Python 3.8+
- 必需的包：`psutil`（用于增强系统指标）
- GPU 采集器需要 NVIDIA GPU 和 `nvidia-smi` 工具

安装依赖：
```bash
pip install psutil
```

## 采集器类型

<details>
<summary><strong>系统采集器</strong></summary>

**文件:** `collectors/system.py`

收集综合系统指标，包括：
- CPU 使用率
- 内存使用率
- 磁盘使用率
- 网络 I/O（发送/接收字节数）
- 系统负载平均值
- CPU 温度（仅限 Linux）
- 系统运行时间
- 主机名和操作系统信息

**主要特性:**
- 跨平台支持（Linux、macOS、Windows）
- 当 `psutil` 不可用时的降级模式（返回模拟数据）
- 实时指标采集
- 依赖缺失时自动警告

**环境要求:**
- **可选**: `psutil` 库用于准确指标
- 如果未安装 `psutil`，采集器返回模拟值并显示警告

**警告行为:**
- **控制台**: `[WARN] psutil library not installed. System metrics may be inaccurate.`
- **前端**: 添加 `status` 字段：`⚠️ Metrics may be simulated - Install psutil: pip install psutil`

**使用示例:**
```bash
python collectors/system.py --host 127.0.0.1 --port 12345 --interval 5
```

**安装依赖:**
```bash
pip install psutil
```

</details>

<details>
<summary><strong>HTTP 存活采集器</strong></summary>

**文件:** `collectors/http_alive.py`

监控 HTTP 端点的可用性：
- 检查 URL 状态码
- 测量响应延迟
- 从 URL 中提取主域名
- 为每个 URL 返回独立状态

**主要特性:**
- 网络状态监控
- 域名提取以获得更清晰的输出
- 每个 URL 独立状态报告
- 网络不可用时自动警告

**环境要求:**
- 能够访问目标 URL 的网络连接
- 无需外部依赖

**警告行为:**
- **控制台**: `[WARN] HTTP Alive Collector: Cannot reach {url} - network may be unavailable`
- **前端**: 返回状态消息：`{domain}\n⚠️ Network Error\nNetwork may be unavailable`

**使用示例:**
```bash
python collectors/http_alive.py --host 127.0.0.1 --port 12345 --urls https://example.com https://google.com
```

</details>

<details>
<summary><strong>GPU 采集器</strong></summary>

**文件:** `collectors/gpu.py`

监控 NVIDIA GPU 状态：
- 显存使用情况（已用/总量）
- GPU 使用率
- GPU 温度
- 运行进程检测及变更日志

**主要特性:**
- 自动检测 NVIDIA GPU
- 进程变更监控（带冷却机制）
- 每个 GPU 独立状态报告
- NVIDIA GPU 不可用时自动警告

**环境要求:**
- NVIDIA GPU 硬件
- 安装 `nvidia-smi` 工具（通常随 NVIDIA 驱动一起安装）

**警告行为:**
- **控制台**: `[WARN] NVIDIA GPU not detected. Please install NVIDIA drivers and nvidia-smi tool.`
- **前端**: 返回状态消息：`⚠️ GPU Unavailable - Please install NVIDIA drivers`

**使用示例:**
```bash
python collectors/gpu.py --host 127.0.0.1 --port 12345 --interval 5 --process-log-interval 60
```

**安装:**
- 安装适用于您 GPU 的 NVIDIA 驱动
- `nvidia-smi` 通常随 NVIDIA 驱动一起安装

</details>

<details>
<summary><strong>本地存储采集器</strong></summary>

**文件:** `collectors/local_storage.py`

收集系统统计信息并具备本地存储能力：
- CPU 和内存使用
- 自动数据持久化
- 失败数据缓存
- 历史指标追踪

**主要特性:**
- 继承自 `StorageCollector`
- 启动时自动重试
- 数据备份和恢复

**使用示例:**
```bash
python collectors/local_storage.py --host 127.0.0.1 --port 12345 --storage-path ./data
```

</details>

## 运行采集器

### 独立运行

每个采集器可以独立运行：

```bash
# 系统采集器
python collectors/system.py --host 127.0.0.1 --port 12345 --interval 5

# HTTP 存活采集器
python collectors/http_alive.py --host 127.0.0.1 --port 12345 --urls https://example.com https://google.com

# GPU 采集器
python collectors/gpu.py --host 127.0.0.1 --port 12345 --interval 5

# 本地存储采集器
python collectors/local_storage.py --host 127.0.0.1 --port 12345 --storage-path ./data
```

### 通过网关运行

使用 `run_gateway.py` 启动网关和所有采集器：

```bash
# 使用默认设置启动网关
python run_gateway.py

# 在指定端口启动网关
python run_gateway.py --port 12345
```

## 如何引用示例采集器

您可以通过多种方式在自己的项目中引用和使用示例采集器：

### 导入采集器

```python
# 导入单个采集器
from collectors.system import SystemCollector
from collectors.http_alive import HttpAliveCollector
from collectors.gpu import GPUCollector
from collectors.local_storage import SystemStatsCollector

# 创建实例
system_collector = SystemCollector(host="127.0.0.1", port=12345, interval=5)
http_collector = HttpAliveCollector(urls=["https://example.com"])
```

### 将采集器作为模块使用

```python
# 以编程方式运行采集器
collector = SystemCollector()
metrics = collector.collect()
print(metrics)

# 访问基类功能
collector.send_tcp_message("Hello from collector")
collector.alert("WARNING", "High CPU", "CPU usage exceeded 90%")
```

### 扩展现有采集器

```python
from collectors.system import SystemCollector

class CustomSystemCollector(SystemCollector):
    def collect(self):
        # 调用父类方法
        metrics = super().collect()
        # 添加自定义指标
        metrics["custom_field"] = "custom_value"
        return metrics
```

## 高级开发

<details>
<summary><strong>自定义采集器开发</strong></summary>

### 分步指南

创建自定义采集器：

1. **在 `collectors/` 目录中创建新文件**
2. **从 `collectors.base` 导入基类**
3. **继承** `BaseCollector` 或 `StorageCollector`
4. **实现** `collect()` 方法
5. **可选地重写** `metrics_to_lines()` 进行自定义格式化

### 示例：简单采集器

```python
from collectors.base import BaseCollector
from typing import Dict, Any

class MyCollector(BaseCollector):
    """自定义采集器模板"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 12345, interval: int = 5):
        super().__init__(host, port, interval)
        # 初始化自定义属性
        self._custom_config = {}
    
    def collect(self) -> Dict[str, Any]:
        """收集自定义指标"""
        return {
            "custom_metric": 42,
            "status": "running"
        }
    
    def metrics_to_lines(self, metrics: Dict[str, Any]) -> list:
        """将指标转换为协议行"""
        lines = []
        lines.append(self.format_metric("T", "custom_metric", metrics["custom_metric"]))
        lines.append(self.format_metric("S", "status", metrics["status"]))
        return lines
```

### 添加 CLI 支持

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
<summary><strong>扩展基类</strong></summary>

### BaseCollector 特性

`BaseCollector` 类提供：
- TCP 连接管理
- 指标格式化
- 告警系统
- 错误处理
- 可配置的输出模式

### StorageCollector 特性

`StorageCollector` 类扩展了 `BaseCollector`：
- 本地文件存储
- 数据持久化
- 失败消息缓存
- 历史记录追踪

### 示例：使用存储功能

```python
from collectors.base import StorageCollector

class MyStorageCollector(StorageCollector):
    def collect(self):
        # 你的采集逻辑
        data = {"value": 100}
        
        # 保存到历史记录
        self._save_to_history(data)
        
        # 缓存失败数据（如果需要）
        # self._cache_failed_data("error message")
        
        return data
```

### 重写基类方法

```python
from collectors.base import BaseCollector

class AdvancedCollector(BaseCollector):
    def _on_success(self, metrics):
        """自定义成功回调"""
        print(f"Successfully collected: {len(metrics)} metrics")
    
    def _on_failure(self, error):
        """自定义失败回调"""
        print(f"Collection failed: {error}")
        # 发送告警
        self.alert("ERROR", "Collection Failed", str(error))
```

</details>

<details>
<summary><strong>最佳实践</strong></summary>

### 代码组织

1. **单一职责**: 每个采集器应专注于一种类型的指标采集
2. **错误处理**: 始终优雅地处理异常
3. **日志记录**: 使用适当的日志记录进行调试
4. **配置管理**: 使可配置参数明确
5. **测试**: 为自定义采集器编写单元测试

### 性能考虑

1. **避免阻塞调用**: 对 I/O 密集型任务使用异步操作
2. **批处理**: 分组相关操作
3. **资源管理**: 正确释放资源
4. **间隔控制**: 使用适当的采集间隔

### 安全实践

1. **输入验证**: 验证所有输入
2. **安全通信**: 对外部调用使用 HTTPS
3. **密钥管理**: 不要硬编码敏感数据
4. **最小权限**: 以最小权限运行采集器

### 测试指南

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

## 告警系统使用指南

### 告警功能概述

`BaseCollector` 基类提供了完整的告警系统，子类可以直接调用 `self.alert()` 方法发送告警。告警支持以下特性：

- **四种告警级别**: INFO, WARNING, ERROR, CRITICAL
- **冷却机制**: 同一指标的告警会自动冷却，避免重复发送
- **多种输出方式**: 控制台输出(stdout)和 Webhook 通知
- **自动去重**: 基于告警级别和指标名称进行去重

### 告警配置

告警配置在 `run_gateway.py` 中：

```python
ALERT_CONFIG = {
    "enabled": True,                    # 启用/禁用告警
    "type": "stdout",                   # "stdout" 或 "webhook"
    "target": "admin@example.com",      # 告警接收者标识
    "webhook_url": "",                  # 外部通知的 Webhook URL
}
```

### 告警方法签名

```python
def alert(
    self,
    level: str,           # 告警级别: INFO, WARNING, ERROR, CRITICAL
    title: str,           # 告警标题
    message: str,         # 告警消息内容
    metric_name: str = None,   # 关联的指标名称（用于去重）
    metric_value: Any = None   # 关联的指标值
)
```

### 在子类中发送告警

以下是在自定义采集器中使用告警的完整示例：

```python
from collectors.base import BaseCollector
from typing import Dict, Any

class MyCollector(BaseCollector):
    """自定义采集器，演示告警功能"""
    
    def __init__(self, host="127.0.0.1", port=12345, interval=5):
        super().__init__(host, port, interval)
        # 配置告警（通常由 run_gateway.py 统一配置）
        self.set_alert_config({
            "enabled": True,
            "type": "stdout",
            "target": "admin@example.com"
        })
    
    def collect(self) -> Dict[str, Any]:
        # 模拟采集数据
        cpu_usage = 95.5  # 模拟高 CPU 使用率
        
        # 检测异常并发送告警
        if cpu_usage > 90:
            self.alert(
                level="WARNING",
                title="High CPU Usage",
                message=f"CPU usage is {cpu_usage}%, which exceeds the threshold of 90%",
                metric_name="cpu_percent",
                metric_value=cpu_usage
            )
        
        # 严重异常
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

### 告警冷却机制

基类内置了告警冷却机制，默认冷却时间为 300 秒（5分钟）：

```python
# 在基类中的实现
self._alert_cooldown = 300  # 冷却时间（秒）

# 告警时会自动检查冷却状态
if time.time() - last_alert < self._alert_cooldown:
    print(f"[ALERT] Alert cooldown active for {key}")
    return  # 跳过发送
```

### 自定义告警冷却时间

```python
class MyCollector(BaseCollector):
    def __init__(self, host="127.0.0.1", port=12345, interval=5):
        super().__init__(host, port, interval)
        # 设置自定义冷却时间（1分钟）
        self._alert_cooldown = 60
```

### Webhook 告警配置

配置 Webhook 方式发送告警：

```python
ALERT_CONFIG = {
    "enabled": True,
    "type": "webhook",
    "target": "ops-team",
    "webhook_url": "https://your-alert-service.com/webhook"
}
```

Webhook 发送的 payload 格式：
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

### 完整示例：带告警的采集器

```python
from collectors.base import BaseCollector
import psutil

class SmartMonitorCollector(BaseCollector):
    """智能监控采集器，带告警功能"""
    
    CPU_WARNING_THRESHOLD = 80
    CPU_CRITICAL_THRESHOLD = 95
    MEM_WARNING_THRESHOLD = 85
    MEM_CRITICAL_THRESHOLD = 95
    
    def collect(self):
        metrics = {}
        
        # 采集 CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics["cpu_percent"] = cpu_percent
        
        # CPU 告警逻辑
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
        
        # 采集内存使用率
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        metrics["mem_percent"] = mem_percent
        
        # 内存告警逻辑
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
        """发送失败时自动告警"""
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

### 告警级别说明

| 级别 | 用途 | 示例场景 |
|------|------|----------|
| **INFO** | 信息性通知 | 服务启动、配置变更 |
| **WARNING** | 警告级别 | 指标超过阈值、性能下降 |
| **ERROR** | 错误级别 | 采集失败、连接异常 |
| **CRITICAL** | 严重级别 | 系统崩溃、资源耗尽 |

## 配置

### 采集器选项

| 采集器 | 选项 | 说明 |
|--------|------|------|
| 系统采集器 | `--host`, `--port`, `--interval` | 网关主机、端口、采集间隔 |
| HTTP 存活采集器 | `--urls` | 要监控的 URL 列表 |
| GPU 采集器 | `--process-log-interval` | 进程变更日志间隔 |
| 本地存储采集器 | `--storage-path` | 本地数据存储路径 |

## 指标类型

| 类型 | 代码 | 说明 |
|------|------|------|
| 状态 | `S` | 字符串状态信息 |
| 趋势 | `T` | 数值用于趋势跟踪 |
| 信息 | `I` | 信息性指标 |
| 日志 | `L` | 日志消息 |

## 输出模式

- **TCP 模式**: 通过 TCP 发送指标到网关
- **Stdout 模式**: 打印指标到控制台（用于调试）

```bash
python collectors/system.py --output stdout
```