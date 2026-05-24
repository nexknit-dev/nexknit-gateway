#!/usr/bin/env python3
"""Nexknit 示例采集器 - 短连接版
网关采用短连接模式：每条消息独立TCP连接，发送后立即关闭
本采集器针对此特性优化：每批数据建立一次连接，快速发送后关闭连接"""

import argparse
import os
import socket
import sys
import time
import platform
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple


SYSTEM = platform.system()

HAS_PSUTIL = False
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    pass


def print_banner():
    """Print startup banner with backend info."""
    backend = "psutil" if HAS_PSUTIL else "stdlib"
    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    Nexknit Collector Template                    ║
╠══════════════════════════════════════════════════════════════════╣
║ Backend: {backend:<54}                                           ║
║ Platform: {platform.system()} {platform.release():<45}           ║
║ If you find this project useful, please give us a star!          ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)
    if not HAS_PSUTIL:
        print("[INFO] Running in stdlib fallback mode - some metrics may be simulated\n")


class CPUMeter:
    """CPU 使用率采集器"""

    _prev_total: int = 0
    _prev_idle: int = 0
    _initialized: bool = False

    def __init__(self):
        if HAS_PSUTIL:
            self._collect = self._psutil_cpu
        elif SYSTEM == "Linux":
            self._collect = self._linux_cpu
        elif SYSTEM == "Darwin":
            self._collect = self._darwin_cpu
        elif SYSTEM == "Windows":
            self._collect = self._windows_cpu
        else:
            self._collect = self._fallback_cpu

    def _psutil_cpu(self) -> float:
        return psutil.cpu_percent(interval=0.1)

    def _linux_cpu(self) -> float:
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            fields = [float(x) for x in line.split()[1:]]
            total = sum(fields)
            idle = fields[3]

            if not CPUMeter._initialized:
                CPUMeter._prev_total, CPUMeter._prev_idle = total, idle
                CPUMeter._initialized = True
                return 0.0

            delta_total = total - CPUMeter._prev_total
            delta_idle = idle - CPUMeter._prev_idle
            CPUMeter._prev_total, CPUMeter._prev_idle = total, idle

            if delta_total == 0:
                return 0.0
            return max(0.0, min(100.0, (1 - delta_idle / delta_total) * 100))
        except:
            return self._fallback_cpu()

    def _darwin_cpu(self) -> float:
        try:
            t1 = os.times()
            time.sleep(0.1)
            t2 = os.times()
            delta_idle = t2.idle - t1.idle
            delta_total = (t2.user - t1.user) + (t2.system - t1.system) + delta_idle
            if delta_total == 0:
                return 0.0
            return max(0.0, min(100.0, (1 - delta_idle / delta_total) * 100))
        except:
            return self._fallback_cpu()

    def _windows_cpu(self) -> float:
        try:
            t1 = os.times()
            time.sleep(0.1)
            t2 = os.times()
            delta = (t2.user - t1.user) + (t2.system - t1.system)
            total = delta + (t2.idle - t1.idle)
            if total == 0:
                return 0.0
            return max(0.0, min(100.0, delta / total * 100))
        except:
            return self._fallback_cpu()

    @staticmethod
    def _fallback_cpu() -> float:
        return round(20 + (hash(time.time()) % 60), 1)

    def get(self) -> float:
        return round(self._collect(), 1)


class MemoryMeter:
    """内存使用率采集器"""

    _cached_memory: Tuple[int, int] = (0, 0)
    _last_update: float = 0

    def __init__(self):
        if HAS_PSUTIL:
            self._collect = self._psutil_memory
        elif SYSTEM == "Linux":
            self._collect = self._linux_memory
        elif SYSTEM == "Darwin":
            self._collect = self._darwin_memory
        elif SYSTEM == "Windows":
            self._collect = self._windows_memory
        else:
            self._collect = self._fallback_memory

    def _psutil_memory(self) -> float:
        return psutil.virtual_memory().percent

    @staticmethod
    def _linux_memory() -> float:
        try:
            with open("/proc/meminfo", "r") as f:
                mem = {}
                for line in f:
                    parts = line.split()
                    mem[parts[0].rstrip(":")] = int(parts[1])
            total = mem.get("MemTotal", 1)
            available = mem.get("MemAvailable", mem.get("MemFree", 0))
            return round((total - available) / total * 100, 1)
        except:
            return round(30 + (hash(time.time()) % 50), 1)

    @staticmethod
    def _darwin_memory() -> float:
        try:
            vm = subprocess.check_output(["vm_stat"], text=True, timeout=5)
            lines = vm.strip().split("\n")
            pages = {}
            for line in lines:
                if ":" in line:
                    key = line.split(":")[0].strip()
                    val = int(re.search(r"\d+", line.split(":")[1].rstrip(".")).group())
                    pages[key] = val * 4096
            total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip())
            used = pages.get("Pages active", 0) + pages.get("Pages inactive", 0) + pages.get("Pages wired", 0)
            return round(used / total * 100, 1)
        except:
            return round(30 + (hash(time.time()) % 50), 1)

    @staticmethod
    def _windows_memory() -> float:
        try:
            import ctypes
            class MemStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_uint32), ("dwMemoryLoad", ctypes.c_uint32),
                            ("ullTotalPhys", ctypes.c_uint64), ("ullAvailPhys", ctypes.c_uint64)]
            m = MemStatus()
            m.dwLength = ctypes.sizeof(MemStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            if m.ullTotalPhys > 0:
                return round((m.ullTotalPhys - m.ullAvailPhys) / m.ullTotalPhys * 100, 1)
            return round(30 + (hash(time.time()) % 50), 1)
        except:
            return round(30 + (hash(time.time()) % 50), 1)

    @staticmethod
    def _fallback_memory() -> float:
        return round(30 + (hash(time.time()) % 50), 1)

    def get(self) -> float:
        return self._collect()


class DiskMeter:
    """磁盘使用率采集器"""
    
    def __init__(self):
        if SYSTEM == "Linux" or SYSTEM == "Darwin":
            self._collect = self._unix_disk
        elif SYSTEM == "Windows":
            self._collect = self._windows_disk
        else:
            self._collect = self._fallback_disk
    
    @staticmethod
    def _unix_disk() -> float:
        try:
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bfree * stat.f_frsize
            return round((total - free) / total * 100, 1) if total > 0 else 0.0
        except:
            return 50.0
    
    @staticmethod
    def _windows_disk() -> float:
        try:
            import ctypes
            free = ctypes.c_uint64(0)
            total = ctypes.c_uint64(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p("C:\\"), None, ctypes.pointer(total), ctypes.pointer(free))
            return round((total.value - free.value) / total.value * 100, 1) if total.value > 0 else 0.0
        except:
            return 50.0
    
    @staticmethod
    def _fallback_disk() -> float:
        return 50.0
    
    def get(self) -> float:
        return self._collect()


class NetworkMeter:
    """网络 I/O 采集器"""
    
    def __init__(self):
        self._prev_sent = 0
        self._prev_recv = 0
        self._initialized = False
        
        if SYSTEM == "Linux":
            self._collect = self._linux_net
        elif SYSTEM == "Darwin":
            self._collect = self._darwin_net
        elif SYSTEM == "Windows":
            self._collect = self._windows_net
        else:
            self._collect = self._fallback_net
    
    @staticmethod
    def _linux_net() -> tuple:
        try:
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()[2:]
            sent = recv = 0
            for line in lines:
                parts = line.split()
                if len(parts) >= 10 and parts[0].rstrip(":") != "lo":
                    recv += int(parts[1])
                    sent += int(parts[9])
            return sent, recv
        except:
            return 0, 0
    
    @staticmethod
    def _darwin_net() -> tuple:
        try:
            net = subprocess.check_output(["netstat", "-ib"], text=True, timeout=5)
            lines = net.strip().split("\n")[1:]
            sent = recv = 0
            for line in lines:
                parts = line.split()
                if len(parts) >= 7 and parts[0] != "lo0":
                    try:
                        recv += int(parts[6])
                        sent += int(parts[9]) if len(parts) > 9 else 0
                    except (ValueError, IndexError):
                        continue
            return sent, recv
        except:
            return 0, 0
    
    @staticmethod
    def _windows_net() -> tuple:
        try:
            net = subprocess.check_output(["netstat", "-e"], text=True, timeout=5)
            for line in net.strip().split("\n"):
                if "Bytes" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        return int(parts[3]), int(parts[2])
            return 0, 0
        except:
            return 0, 0
    
    @staticmethod
    def _fallback_net() -> tuple:
        return 0, 0
    
    def get(self) -> tuple:
        sent, recv = self._collect()
        if not self._initialized:
            self._prev_sent, self._prev_recv = sent, recv
            self._initialized = True
            time.sleep(0.1)
            sent, recv = self._collect()
        delta_sent = max(0, sent - self._prev_sent)
        delta_recv = max(0, recv - self._prev_recv)
        self._prev_sent, self._prev_recv = sent, recv
        return delta_sent, delta_recv


class LoadMeter:
    """系统负载采集器"""
    
    def __init__(self):
        if SYSTEM == "Linux":
            self._collect = self._linux_load
        elif SYSTEM == "Darwin":
            self._collect = self._darwin_load
        elif SYSTEM == "Windows":
            self._collect = self._windows_load
        else:
            self._collect = self._fallback_load
    
    @staticmethod
    def _linux_load() -> float:
        try:
            with open("/proc/loadavg") as f:
                return float(f.read().split()[0])
        except:
            return 1.0
    
    @staticmethod
    def _darwin_load() -> float:
        try:
            return float(subprocess.check_output(["sysctl", "-n", "vm.loadavg"], text=True, timeout=5).split()[0])
        except:
            return 1.0
    
    @staticmethod
    def _windows_load() -> float:
        try:
            t1 = os.times()
            time.sleep(0.5)
            t2 = os.times()
            return round(((t2.user - t1.user) + (t2.system - t1.system)) / 0.5, 2)
        except:
            return 1.0
    
    @staticmethod
    def _fallback_load() -> float:
        return 1.0
    
    def get(self) -> float:
        return round(self._collect(), 2)


class CPUTempMeter:
    """CPU 温度采集器"""
    
    def __init__(self):
        if SYSTEM == "Linux":
            self._temps = self._linux_find_temps()
            self._collect = self._linux_temp if self._temps else self._fallback_temp
        elif SYSTEM == "Darwin":
            self._collect = self._darwin_temp
        elif SYSTEM == "Windows":
            self._collect = self._windows_temp
        else:
            self._collect = self._fallback_temp
    
    @staticmethod
    def _linux_find_temps() -> list:
        temps = []
        thermal = Path("/sys/class/thermal")
        if thermal.exists():
            for zone in thermal.glob("thermal_zone*"):
                temp_file = zone / "temp"
                if temp_file.exists():
                    temps.append(str(temp_file))
        return temps
    
    @staticmethod
    def _linux_temp() -> float:
        for temp_file in CPUTempMeter._linux_find_temps():
            try:
                with open(temp_file, "r") as f:
                    return round(int(f.read().strip()) / 1000.0, 1)
            except:
                pass
        return 60.0
    
    @staticmethod
    def _darwin_temp() -> float:
        return 60.0
    
    @staticmethod
    def _windows_temp() -> float:
        return 60.0
    
    @staticmethod
    def _fallback_temp() -> float:
        return 60.0
    
    def get(self) -> float:
        return self._collect()


class UptimeMeter:
    """系统运行时间采集器"""
    
    def __init__(self):
        if SYSTEM == "Linux":
            self._collect = self._linux_uptime
        elif SYSTEM == "Darwin":
            self._collect = self._darwin_uptime
        elif SYSTEM == "Windows":
            self._collect = self._windows_uptime
        else:
            self._collect = self._fallback_uptime
    
    @staticmethod
    def _linux_uptime() -> int:
        try:
            with open("/proc/uptime", "r") as f:
                return int(float(f.read().split()[0]))
        except:
            return 0
    
    @staticmethod
    def _darwin_uptime() -> int:
        try:
            boot = subprocess.check_output(["sysctl", "-n", "kern.boottime"], text=True, timeout=5)
            match = re.search(r"sec = (\d+)", boot)
            return int(time.time() - int(match.group(1))) if match else 0
        except:
            return 0
    
    @staticmethod
    def _windows_uptime() -> int:
        try:
            uptime = subprocess.check_output(
                ["powershell", "-Command", "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | Select-Object -ExpandProperty TotalSeconds"],
                text=True, timeout=5
            ).strip()
            return int(float(uptime))
        except:
            return 0
    
    @staticmethod
    def _fallback_uptime() -> int:
        return int(time.time() - 3600)
    
    def get(self) -> int:
        return self._collect()


class SystemCollector:
    """系统指标采集器"""
    
    def __init__(self):
        self.cpu = CPUMeter()
        self.memory = MemoryMeter()
        self.disk = DiskMeter()
        self.network = NetworkMeter()
        self.load = LoadMeter()
        self.temp = CPUTempMeter()
        self.uptime = UptimeMeter()
    
    def collect(self) -> Dict[str, Any]:
        net_sent, net_recv = self.network.get()
        return {
            "cpu_percent": self.cpu.get(),
            "memory_percent": self.memory.get(),
            "disk_percent": self.disk.get(),
            "cpu_temp": self.temp.get(),
            "network_sent": max(0, net_sent),
            "network_recv": max(0, net_recv),
            "load_avg": self.load.get(),
            "hostname": platform.node(),
            "os_version": f"{platform.system()} {platform.release()}",
            "uptime_seconds": self.uptime.get(),
            "boot_time": int(time.time() - self.uptime.get()),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count() or 1,
        }


def send_tcp_message(host: str, port: int, message: str) -> bool:
    """发送单条TCP消息（短连接模式）"""
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            sock.connect((host, port))
            sock.sendall(message.encode("utf-8"))
        return True
    except Exception:
        return False


def send_metrics_tcp(host: str, port: int, metrics: Dict[str, Any]) -> bool:
    """通过TCP发送所有指标（短连接模式：每条消息独立连接）"""
    
    lines = []
    lines.append(f"T|cpu_percent|{metrics['cpu_percent']}")
    lines.append(f"T|memory_percent|{metrics['memory_percent']}")
    lines.append(f"I|disk_percent|{metrics['disk_percent']}")
    lines.append(f"S|hostname|{metrics['hostname']}")
    lines.append(f"S|os_version|{metrics['os_version']}")
    lines.append(f"S|uptime_seconds|{metrics['uptime_seconds']}")
    lines.append(f"S|cpu_count|{metrics['cpu_count']}")
    lines.append(f"S|platform|{metrics['platform']}")
    lines.append(f"L|boot_time|{datetime.fromtimestamp(metrics['boot_time']).isoformat()}")
    
    success = True
    for line in lines:
        if not send_tcp_message(host, port, line + "\n"):
            success = False
    return success


def run_collector(host: str, port: int, interval: int, output_mode: str = "tcp"):
    """运行采集主循环"""

    
    collector = SystemCollector()

    print_banner()

    print(f"[INFO] Target: {host}:{port}")
    print(f"[INFO] Interval: {interval}s")
    print(f"[INFO] Mode: {'TCP' if output_mode == 'tcp' else 'STDOUT'}\n")

    consecutive_failures = 0
    max_failures = 3
    
    while True:
        try:
            metrics = collector.collect()
            
            if output_mode == "tcp":
                success = send_metrics_tcp(host, port, metrics)
                
                if success:
                    consecutive_failures = 0
                    print(
                        f"[SEND] CPU: {metrics['cpu_percent']}% | "
                        f"MEM: {metrics['memory_percent']}% | "
                        f"DISK: {metrics['disk_percent']}%"
                    )
                else:
                    consecutive_failures += 1
                    print(f"[FAIL] Send failed (attempt {consecutive_failures}/{max_failures})")
                    if consecutive_failures >= max_failures:
                        print(f"[WARN] Too many failures, switching to stdout mode")
                        output_mode = "stdout"
            else:
                print(f"T|cpu_percent|{metrics['cpu_percent']}")
                print(f"T|memory_percent|{metrics['memory_percent']}")
                print(f"I|disk_percent|{metrics['disk_percent']}")
                consecutive_failures = 0
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n[INFO] Collector stopped by user")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Nexknit 示例采集器 (短连接模式)")
    parser.add_argument("--host", default="127.0.0.1", help="网关地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=12345, help="网关端口 (默认: 12345)")
    parser.add_argument("--interval", type=int, default=5, help="采集间隔秒数 (默认: 5)")
    parser.add_argument("--output", choices=["tcp", "stdout"], default="tcp", help="输出模式 (默认: tcp)")
    args = parser.parse_args()
    run_collector(args.host, args.port, args.interval, args.output)


if __name__ == "__main__":
    main()
